"""Airtable API client with OAuth 2.0 authentication."""

import asyncio
import logging
import time
from typing import Any, Protocol

import httpx
from pydantic import ValidationError

from .exceptions import (
    AirtableAPIError,
    AirtableAuthError,
    AirtableNotFoundError,
    AirtableRateLimitError,
    AirtableValidationError,
)
from .models import (
    AirtableRecord,
    BaseSchemaResponse,
    CreateRecordsRequest,
    CreateRecordsResponse,
    DeleteRecordsResponse,
    ListBasesResponse,
    ListRecordsOptions,
    ListRecordsResponse,
    UpdateRecordsRequest,
    UpdateRecordsResponse,
)

logger = logging.getLogger(__name__)


class OAuthHandler(Protocol):
    """Protocol for OAuth handlers used by AirtableClient."""

    async def ensure_valid_token(self) -> bool:
        """Ensure the access token is valid, refreshing if necessary."""
        ...

    @property
    def access_token(self) -> str | None:
        """Get the current access token."""
        ...


# Airtable API configuration
AIRTABLE_BASE_URL = "https://api.airtable.com"
RATE_LIMIT_REQUESTS_PER_SECOND = 5
RATE_LIMIT_WINDOW = 1.0  # 1 second


class AirtableClient:
    """Airtable API client with OAuth 2.0 authentication and rate limiting.

    This client provides async methods for interacting with the Airtable API:
    - Base operations (list bases, get schema)
    - Record operations (CRUD operations)
    - Built-in rate limiting and retry logic
    - Comprehensive error handling
    """

    def __init__(
        self,
        oauth_handler: OAuthHandler,
        base_url: str = AIRTABLE_BASE_URL,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """Initialize the Airtable client.

        Args:
            oauth_handler: OAuth handler for authentication
            base_url: Airtable API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.oauth_handler = oauth_handler
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries

        # Rate limiting state
        self._last_request_time = 0.0
        self._request_count = 0
        self._rate_limit_window_start = 0.0

    async def _ensure_rate_limit(self) -> None:
        """Ensure we don't exceed rate limits."""
        current_time = time.time()

        # Reset window if needed
        if current_time - self._rate_limit_window_start >= RATE_LIMIT_WINDOW:
            self._rate_limit_window_start = current_time
            self._request_count = 0

        # If we've hit the limit, wait
        if self._request_count >= RATE_LIMIT_REQUESTS_PER_SECOND:
            wait_time = RATE_LIMIT_WINDOW - (
                current_time - self._rate_limit_window_start
            )
            if wait_time > 0:
                logger.debug(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
                # Reset for new window
                self._rate_limit_window_start = time.time()
                self._request_count = 0

        self._request_count += 1
        self._last_request_time = current_time

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        response_model: Any | None = None,
    ) -> dict[str, Any] | Any:
        """Make an authenticated request to the Airtable API.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            response_model: Pydantic model to parse response

        Returns:
            Parsed response data

        Raises:
            AirtableAPIError: For API errors
            AirtableAuthError: For authentication errors
            AirtableRateLimitError: For rate limit errors
        """
        # Ensure valid authentication
        if not await self.oauth_handler.ensure_valid_token():
            raise AirtableAuthError("Failed to obtain valid access token")

        # Apply rate limiting
        await self._ensure_rate_limit()

        url = f"{self.base_url}{endpoint}"

        # Prepare headers
        headers = self.oauth_handler.get_auth_headers()
        headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

        # Prepare request kwargs
        request_kwargs = {
            "method": method,
            "url": url,
            "headers": headers,
            "timeout": self.timeout,
        }

        if data:
            request_kwargs["json"] = data

        if params:
            request_kwargs["params"] = params

        # Retry logic
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.request(**request_kwargs)

                    # Handle different status codes
                    if response.status_code == 401:
                        raise AirtableAuthError(
                            "Authentication failed - invalid or expired token"
                        )
                    elif response.status_code == 404:
                        raise AirtableNotFoundError(f"Resource not found: {url}")
                    elif response.status_code == 422:
                        error_text = response.text
                        raise AirtableValidationError(f"Validation error: {error_text}")
                    elif response.status_code == 429:
                        retry_after = int(response.headers.get("Retry-After", 30))
                        raise AirtableRateLimitError(
                            "Rate limit exceeded", retry_after=retry_after
                        )
                    elif not response.is_success:
                        error_text = response.text
                        raise AirtableAPIError(
                            f"API request failed: {response.status_code} {response.reason_phrase}",
                            status_code=response.status_code,
                            response_text=error_text,
                        )

                    # Parse response
                    try:
                        response_data = response.json()
                    except Exception as e:
                        raise AirtableAPIError(
                            f"Failed to parse JSON response: {e}"
                        ) from e

                    # Validate response with Pydantic model if provided
                    if response_model:
                        try:
                            return response_model.model_validate(response_data)
                        except ValidationError as e:
                            raise AirtableAPIError(
                                f"Response validation error: {e}"
                            ) from e

                    return response_data

            except AirtableRateLimitError as e:
                # Handle rate limit with backoff
                if attempt < self.max_retries:
                    wait_time = e.retry_after or (2**attempt)
                    logger.warning(f"Rate limited, retrying in {wait_time} seconds")
                    await asyncio.sleep(wait_time)
                    continue
                raise

            except (httpx.RequestError, httpx.TimeoutException) as e:
                last_exception = e
                if attempt < self.max_retries:
                    wait_time = 2**attempt  # Exponential backoff
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}), retrying in {wait_time} seconds: {e}"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                break

        # If we get here, all retries failed
        raise AirtableAPIError(
            f"Request failed after {self.max_retries + 1} attempts: {last_exception}"
        )

    async def list_bases(self) -> ListBasesResponse:
        """List all accessible Airtable bases.

        Returns:
            Response containing list of bases
        """
        logger.info("Listing Airtable bases")
        return await self._make_request(
            "GET",
            "/v0/meta/bases",
            response_model=ListBasesResponse,
        )

    async def get_base_schema(self, base_id: str) -> BaseSchemaResponse:
        """Get schema information for a specific base.

        Args:
            base_id: The Airtable base ID

        Returns:
            Response containing base schema (tables and fields)
        """
        logger.info(f"Getting schema for base {base_id}")
        return await self._make_request(
            "GET",
            f"/v0/meta/bases/{base_id}/tables",
            response_model=BaseSchemaResponse,
        )

    async def list_records(
        self,
        base_id: str,
        table_id: str,
        options: ListRecordsOptions | None = None,
    ) -> list[AirtableRecord]:
        """List records from a table with pagination support.

        Args:
            base_id: The Airtable base ID
            table_id: The table ID or name
            options: Options for filtering and pagination

        Returns:
            List of records
        """
        logger.info(f"Listing records from {base_id}/{table_id}")

        all_records = []
        offset = None

        while True:
            # Build query parameters
            params = {}
            if options:
                # Convert Pydantic model to dict and filter None values
                option_dict = options.model_dump(by_alias=True, exclude_none=True)

                # Handle array parameters specially for Airtable API
                for key, value in option_dict.items():
                    if key == "fields" and isinstance(value, list):
                        # Airtable expects fields as multiple parameters: fields[]=field1&fields[]=field2
                        params[key] = value
                    elif key == "sort" and isinstance(value, list):
                        # Airtable expects sort as indexed parameters: sort[0][field]=Name&sort[0][direction]=asc
                        for i, sort_item in enumerate(value):
                            if isinstance(sort_item, dict):
                                for sort_key, sort_value in sort_item.items():
                                    params[f"sort[{i}][{sort_key}]"] = sort_value
                    else:
                        params[key] = value

            if offset:
                params["offset"] = offset

            # Debug: Log the parameters being sent to Airtable
            logger.debug(f"Sending request to Airtable with params: {params}")

            response = await self._make_request(
                "GET",
                f"/v0/{base_id}/{table_id}",
                params=params,
                response_model=ListRecordsResponse,
            )

            all_records.extend(response.records)

            # Check if there are more records
            if not response.offset:
                break

            offset = response.offset

            # Respect maxRecords if specified
            if (
                options
                and options.max_records
                and len(all_records) >= options.max_records
            ):
                all_records = all_records[: options.max_records]
                break

        return all_records

    async def get_record(
        self,
        base_id: str,
        table_id: str,
        record_id: str,
    ) -> AirtableRecord:
        """Get a specific record by ID.

        Args:
            base_id: The Airtable base ID
            table_id: The table ID or name
            record_id: The record ID

        Returns:
            The requested record
        """
        logger.info(f"Getting record {record_id} from {base_id}/{table_id}")

        response = await self._make_request(
            "GET",
            f"/v0/{base_id}/{table_id}/{record_id}",
            response_model=AirtableRecord,
        )

        return response

    async def create_records(
        self,
        base_id: str,
        table_id: str,
        records: list[dict[str, Any]],
        typecast: bool = False,
    ) -> list[AirtableRecord]:
        """Create new records in a table.

        Args:
            base_id: The Airtable base ID
            table_id: The table ID or name
            records: List of record data (each should have 'fields' key)
            typecast: Whether to enable automatic data conversion

        Returns:
            List of created records
        """
        logger.info(f"Creating {len(records)} records in {base_id}/{table_id}")

        request_data = CreateRecordsRequest(
            records=records,
            typecast=typecast,
        )

        response = await self._make_request(
            "POST",
            f"/v0/{base_id}/{table_id}",
            data=request_data.model_dump(by_alias=True, exclude_none=True),
            response_model=CreateRecordsResponse,
        )

        return response.records

    async def update_records(
        self,
        base_id: str,
        table_id: str,
        records: list[dict[str, Any]],
        typecast: bool = False,
    ) -> list[AirtableRecord]:
        """Update existing records in a table.

        Args:
            base_id: The Airtable base ID
            table_id: The table ID or name
            records: List of record updates (each should have 'id' and 'fields' keys)
            typecast: Whether to enable automatic data conversion

        Returns:
            List of updated records
        """
        logger.info(f"Updating {len(records)} records in {base_id}/{table_id}")

        request_data = UpdateRecordsRequest(
            records=records,
            typecast=typecast,
        )

        response = await self._make_request(
            "PATCH",
            f"/v0/{base_id}/{table_id}",
            data=request_data.model_dump(by_alias=True, exclude_none=True),
            response_model=UpdateRecordsResponse,
        )

        return response.records

    async def delete_records(
        self,
        base_id: str,
        table_id: str,
        record_ids: list[str],
    ) -> list[str]:
        """Delete records from a table.

        Args:
            base_id: The Airtable base ID
            table_id: The table ID or name
            record_ids: List of record IDs to delete

        Returns:
            List of deleted record IDs
        """
        logger.info(f"Deleting {len(record_ids)} records from {base_id}/{table_id}")

        params = {"records[]": record_ids}

        response = await self._make_request(
            "DELETE",
            f"/v0/{base_id}/{table_id}",
            params=params,
            response_model=DeleteRecordsResponse,
        )

        return [record["id"] for record in response.records]

    async def search_records(
        self,
        base_id: str,
        table_id: str,
        filter_by_formula: str,
        options: ListRecordsOptions | None = None,
    ) -> list[AirtableRecord]:
        """Search records using a formula filter.

        Args:
            base_id: The Airtable base ID
            table_id: The table ID or name
            filter_by_formula: Airtable formula for filtering
            options: Additional options for the search

        Returns:
            List of matching records
        """
        logger.info(
            f"Searching records in {base_id}/{table_id} with formula: {filter_by_formula}"
        )

        # Merge filter with existing options
        search_options = options or ListRecordsOptions()
        search_options.filter_by_formula = filter_by_formula

        return await self.list_records(base_id, table_id, search_options)
