"""
Main SDK Client
Provides high-level interface to Redlen Sensor API
"""
import time
from typing import Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import (
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    ServerError,
    NetworkError
)
from .resources import SensorResource, ReadingResource, AnalyticsResource


class SensorClient:
    """
    Main SDK client for Redlen Sensor API
    
    Example:
        client = SensorClient(api_key="your-key")
        sensors = client.sensors.list()
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.redlen.com",
        timeout: int = 30,
        max_retries: int = 3,
        verify_ssl: bool = True
    ):
        """
        Initialize SDK client
        
        Args:
            api_key: API authentication key
            base_url: Base URL for API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
            verify_ssl: Whether to verify SSL certificates
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        
        # Setup session with retry logic
        self.session = self._create_session(max_retries)
        
        # Initialize resource endpoints
        self.sensors = SensorResource(self)
        self.readings = ReadingResource(self)
        self.analytics = AnalyticsResource(self)
    
    def _create_session(self, max_retries: int) -> requests.Session:
        """Create requests session with retry logic"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,  # Exponential backoff: 1s, 2s, 4s
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Redlen-SDK/1.0.0"
        })
        
        return session
    
    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json: Optional[dict] = None,
        **kwargs
    ) -> dict:
        """
        Make HTTP request with error handling
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            json: JSON body
            **kwargs: Additional request arguments
        
        Returns:
            Response data as dictionary
        
        Raises:
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit exceeded
            NotFoundError: If resource not found
            ValidationError: If request validation fails
            ServerError: If server error occurs
            NetworkError: If network request fails
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                timeout=self.timeout,
                verify=self.verify_ssl,
                **kwargs
            )
            
            # Handle different status codes
            if response.status_code == 200 or response.status_code == 201:
                return response.json()
            
            elif response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed. Check your API key.",
                    status_code=401,
                    response=response.json()
                )
            
            elif response.status_code == 404:
                raise NotFoundError(
                    "Resource not found",
                    status_code=404,
                    response=response.json()
                )
            
            elif response.status_code == 422:
                raise ValidationError(
                    "Request validation failed",
                    status_code=422,
                    response=response.json()
                )
            
            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                raise RateLimitError(
                    "Rate limit exceeded",
                    status_code=429,
                    retry_after=retry_after,
                    response=response.json()
                )
            
            elif response.status_code >= 500:
                raise ServerError(
                    f"Server error: {response.status_code}",
                    status_code=response.status_code,
                    response=response.json() if response.text else None
                )
            
            else:
                response.raise_for_status()
                return response.json()
        
        except requests.exceptions.Timeout:
            raise NetworkError(f"Request timeout after {self.timeout}s")
        
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"Connection error: {str(e)}")
        
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Network error: {str(e)}")
    
    def close(self):
        """Close the session"""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
