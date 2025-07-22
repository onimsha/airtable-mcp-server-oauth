"""Base OAuth provider interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from ..core.config import ProviderConfig


class BaseOAuthProvider(ABC):
    """Base class for OAuth provider implementations."""
    
    def __init__(self, config: ProviderConfig):
        """Initialize the OAuth provider.
        
        Args:
            config: Provider-specific configuration
        """
        self.config = config
    
    @abstractmethod
    async def exchange_code_for_tokens(
        self,
        code: str,
        code_verifier: Optional[str] = None,
        state: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Exchange authorization code for access tokens.
        
        Args:
            code: Authorization code from provider
            code_verifier: PKCE code verifier
            state: OAuth state parameter
            
        Returns:
            Tuple of (success, token_data)
        """
        pass
    
    @abstractmethod
    async def refresh_access_token(self, refresh_token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Refresh an access token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            Tuple of (success, token_data)
        """
        pass
    
    @abstractmethod
    async def introspect_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Introspect a token to get information about it.
        
        Args:
            token: Token to introspect
            
        Returns:
            Token information or None if invalid
        """
        pass
    
    @abstractmethod
    async def revoke_token(self, token: str) -> bool:
        """Revoke a token.
        
        Args:
            token: Token to revoke
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_authorization_url(
        self,
        state: str,
        code_challenge: Optional[str] = None,
        code_challenge_method: Optional[str] = None,
        **kwargs
    ) -> str:
        """Get authorization URL for the OAuth flow.
        
        Args:
            state: OAuth state parameter
            code_challenge: PKCE code challenge
            code_challenge_method: PKCE challenge method
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Authorization URL
        """
        pass
    
    @abstractmethod
    def get_oauth_metadata(self, server_base_url: str) -> Dict[str, Any]:
        """Get OAuth metadata for discovery.
        
        Args:
            server_base_url: Base URL of the OAuth server
            
        Returns:
            OAuth metadata dictionary
        """
        pass
    
    def get_pkce_requirements(self) -> Dict[str, Any]:
        """Get PKCE requirements for this provider.
        
        Returns:
            PKCE requirements dictionary
        """
        return self.config.get_pkce_requirements()
    
    def get_supported_scopes(self) -> List[str]:
        """Get supported scopes for this provider.
        
        Returns:
            List of supported scopes
        """
        return self.config.get_supported_scopes()
    
    def validate_scope(self, requested_scope: str) -> bool:
        """Validate if requested scope is supported.
        
        Args:
            requested_scope: Space-separated scope string
            
        Returns:
            True if all scopes are supported, False otherwise
        """
        supported = set(self.get_supported_scopes())
        requested = set(requested_scope.split())
        return requested.issubset(supported)