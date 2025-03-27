import requests
import json
from typing import Dict, Any, Optional, Union
from tenacity import retry, stop_after_attempt, wait_exponential

from ..utils.logger import get_logger
from ..utils.config import get_config

logger = get_logger()
config = get_config()

class APIError(Exception):
    """Custom exception for API errors"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error {status_code}: {message}")

class BaseAPIClient:
    """Base API client with common functionality"""
    
    def __init__(self):
        """Initialize the base API client"""
        self.base_url = config.api.base_url
        self.store_config = {
            "customerId": config.api.store_config.customer_id,
            "branchCode": config.api.store_config.branch_code,
            "shipToSequenceNumber": config.api.store_config.ship_to_sequence
        }
        
        # Add authentication headers
        self.auth_headers = {
            "X-Customer-ID": config.api.store_config.customer_id,
            "X-Branch-Code": config.api.store_config.branch_code,
            "X-Ship-To-Sequence": config.api.store_config.ship_to_sequence
        }
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None, 
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request to the API with retry logic
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            headers: Request headers
            
        Returns:
            API response as a dictionary
            
        Raises:
            APIError: If the API returns an error
        """
        url = f"{self.base_url}{endpoint}"
        
        default_headers = {"Content-Type": "application/json"}
        # Add authentication headers
        default_headers.update(self.auth_headers)
        
        if headers:
            default_headers.update(headers)
            
        try:
            logger.debug(f"Making {method} request to {url}")
            if method.upper() == "GET":
                response = requests.get(url, params=params, headers=default_headers)
            elif method.upper() == "POST":
                response = requests.post(url, params=params, json=data, headers=default_headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            try:
                error_detail = e.response.json().get("detail", str(e))
            except json.JSONDecodeError:
                error_detail = str(e)
                
            logger.error(f"API error: {status_code} - {error_detail}")
            raise APIError(status_code, error_detail)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            raise APIError(500, str(e))
            
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GET request to the API
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            API response as a dictionary
        """
        return self._make_request("GET", endpoint, params=params)
        
    def post(self, endpoint: str, data: Dict[str, Any], params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make a POST request to the API
        
        Args:
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            headers: Request headers
            
        Returns:
            API response as a dictionary
        """
        return self._make_request("POST", endpoint, params=params, data=data, headers=headers)
