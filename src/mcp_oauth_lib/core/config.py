"""OAuth configuration classes."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set


@dataclass
class ProviderConfig(ABC):
    """Base configuration for OAuth providers."""
    
    client_id: str
    client_secret: str
    redirect_uri: str
    scope: str
    provider_name: str
    
    @abstractmethod
    def get_authorization_url(self) -> str:
        """Get the provider's authorization URL."""
        pass
    
    @abstractmethod
    def get_token_url(self) -> str:
        """Get the provider's token URL."""
        pass
    
    @abstractmethod
    def get_pkce_requirements(self) -> Dict[str, Any]:
        """Get PKCE requirements for this provider."""
        pass
    
    @abstractmethod
    def get_supported_scopes(self) -> List[str]:
        """Get list of supported scopes for this provider."""
        pass


@dataclass
class OAuthConfig:
    """Main OAuth server configuration."""
    
    server_name: str = "mcp-oauth-server"
    server_version: str = "0.1.0"
    mcp_version: str = "2024-11-05"
    
    # Server configuration
    host: str = "localhost"
    port: int = 8000
    base_url: Optional[str] = None
    
    # OAuth configuration
    state_expiry_seconds: int = 600  # 10 minutes
    auth_code_expiry_seconds: int = 600  # 10 minutes
    
    # Security configuration
    enable_pkce: bool = True
    require_pkce: bool = False
    supported_response_types: List[str] = field(default_factory=lambda: ["code"])
    supported_grant_types: List[str] = field(default_factory=lambda: ["authorization_code", "refresh_token"])
    supported_auth_methods: List[str] = field(default_factory=lambda: ["client_secret_basic", "client_secret_post", "none"])
    
    # Dynamic Client Registration
    enable_dynamic_registration: bool = True
    registration_access_token: Optional[str] = None
    
    # Token management
    token_manager: Optional[Any] = None  # Token storage backend
    
    # CORS configuration
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    cors_methods: List[str] = field(default_factory=lambda: ["GET", "POST", "OPTIONS"])
    cors_headers: List[str] = field(default_factory=lambda: ["Content-Type", "Authorization"])
    
    def get_base_url(self) -> str:
        """Get the server base URL."""
        if self.base_url:
            return self.base_url
        return f"http://{self.host}:{self.port}"
    
    def get_metadata_endpoint(self) -> str:
        """Get the OAuth metadata discovery endpoint."""
        return f"{self.get_base_url()}/.well-known/oauth-authorization-server"
    
    def get_authorization_endpoint(self) -> str:
        """Get the authorization endpoint."""
        return f"{self.get_base_url()}/auth/authorize"
    
    def get_token_endpoint(self) -> str:
        """Get the token endpoint."""
        return f"{self.get_base_url()}/token"
    
    def get_registration_endpoint(self) -> str:
        """Get the dynamic client registration endpoint."""
        return f"{self.get_base_url()}/oauth/register"