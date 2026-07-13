"""
API Client for Majestic RP Marketplace
Handles all HTTP requests to Majestic RP API with error handling and retries
"""

import aiohttp
import logging
from typing import Optional, Dict, Any, List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from config import MAJESTIC_API_BASE_URL, API_TIMEOUT, API_RETRY_ATTEMPTS

logger = logging.getLogger(__name__)


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class MajesticAPIError(Exception):
    """Base exception for Majestic API errors"""
    pass


class InvalidAPIKeyError(MajesticAPIError):
    """Invalid or expired API key (401)"""
    pass


class RateLimitError(MajesticAPIError):
    """Rate limit exceeded (429)"""
    pass


class ForbiddenError(MajesticAPIError):
    """Access forbidden (403)"""
    pass


class NotFoundError(MajesticAPIError):
    """Resource not found (404)"""
    pass


class ServerError(MajesticAPIError):
    """Server error (5xx)"""
    pass


# ============================================================================
# API CLIENT
# ============================================================================

class APIClient:
    """
    Async client for Majestic RP API
    
    Usage:
        async with APIClient(api_key) as client:
            data = await client.get_market_stats("vehicles", 1)
    """
    
    def __init__(self, api_key: str):
        """
        Initialize API client
        
        Args:
            api_key: Majestic RP API key
        """
        self.api_key = api_key
        self.base_url = MAJESTIC_API_BASE_URL
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=API_TIMEOUT)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Majestic-Marketplace-Bot/1.0"
        }
    
    def _handle_error(self, status_code: int, response_data: Dict[str, Any]) -> None:
        """
        Handle HTTP error responses
        
        Args:
            status_code: HTTP status code
            response_data: Response data from API
            
        Raises:
            Appropriate exception based on status code
        """
        error_msg = response_data.get("error", response_data.get("message", "Unknown error"))
        
        if status_code == 401:
            logger.warning(f"Invalid API key: {error_msg}")
            raise InvalidAPIKeyError(f"Неверный API ключ: {error_msg}")
        
        elif status_code == 403:
            logger.warning(f"Access forbidden: {error_msg}")
            raise ForbiddenError(f"Доступ запрещен: {error_msg}")
        
        elif status_code == 404:
            logger.warning(f"Resource not found: {error_msg}")
            raise NotFoundError(f"Ресурс не найден: {error_msg}")
        
        elif status_code == 429:
            logger.warning(f"Rate limit exceeded: {error_msg}")
            raise RateLimitError(f"Превышен лимит запросов. Попробуйте позже.")
        
        elif status_code >= 500:
            logger.error(f"Server error {status_code}: {error_msg}")
            raise ServerError(f"Ошибка сервера Majestic RP. Попробуйте позже.")
        
        else:
            logger.error(f"API error {status_code}: {error_msg}")
            raise MajesticAPIError(f"Ошибка API: {error_msg}")
    
    @retry(
        stop=stop_after_attempt(API_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ServerError, aiohttp.ClientError)),
        before_sleep=lambda rs: logger.warning(f"Retrying request (attempt {rs.attempt_number})")
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to API with retry logic
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            
        Returns:
            Response data as dictionary
            
        Raises:
            Various API exceptions based on response
        """
        if not self.session:
            raise RuntimeError("APIClient not initialized. Use 'async with' context manager.")
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                params=params,
                json=data
            ) as response:
                # Try to parse JSON response
                try:
                    response_data = await response.json()
                except Exception:
                    response_data = {}
                
                # Handle error responses
                if response.status != 200:
                    self._handle_error(response.status, response_data)
                
                logger.debug(f"Successful {method} request to {endpoint}")
                return response_data
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error for {url}: {e}")
            raise MajesticAPIError(f"Ошибка сети при подключении к API")
        
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}", exc_info=True)
            raise MajesticAPIError(f"Неожиданная ошибка: {str(e)}")
    
    # ============================================================================
    # API ENDPOINTS
    # ============================================================================
    
    async def validate_key(self) -> bool:
        """
        Validate API key
        
        Returns:
            True if key is valid, False otherwise
        """
        try:
            await self._request("GET", "auth/validate")
            logger.info("API key validated successfully")
            return True
        except InvalidAPIKeyError:
            logger.warning("API key validation failed")
            return False
        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return False
    
    async def get_market_stats(
        self,
        category: str,
        server: int
    ) -> Dict[str, Any]:
        """
        Get marketplace statistics for category and server
        
        Args:
            category: Category name (vehicles, items, houses, etc.)
            server: Server number
            
        Returns:
            Dictionary with statistics data
        """
        logger.info(f"Fetching market stats for {category} on server {server}")
        
        params = {"server": server}
        data = await self._request("GET", f"market/{category}", params=params)
        
        logger.info(f"Successfully fetched stats for {category} on server {server}")
        return data
    
    async def get_category_listings(
        self,
        category: str,
        server: int,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get listings for a category
        
        Args:
            category: Category name
            server: Server number
            limit: Number of results (max 100)
            offset: Offset for pagination
            
        Returns:
            List of listing dictionaries
        """
        logger.info(f"Fetching listings for {category} on server {server} (limit={limit}, offset={offset})")
        
        params = {
            "server": server,
            "limit": min(limit, 100),  # Ensure we don't exceed API limit
            "offset": offset
        }
        
        data = await self._request("GET", f"market/{category}/listings", params=params)
        listings = data.get("listings", [])
        
        logger.info(f"Successfully fetched {len(listings)} listings for {category}")
        return listings
    
    async def get_item_details(
        self,
        category: str,
        item_id: str,
        server: int
    ) -> Dict[str, Any]:
        """
        Get details for specific item
        
        Args:
            category: Category name
            item_id: Item ID
            server: Server number
            
        Returns:
            Dictionary with item details
        """
        logger.info(f"Fetching details for item {item_id} in {category} on server {server}")
        
        params = {"server": server}
        data = await self._request("GET", f"market/{category}/{item_id}", params=params)
        
        logger.info(f"Successfully fetched details for item {item_id}")
        return data
    
    async def get_price_history(
        self,
        category: str,
        item_id: str,
        server: int,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get price history for an item
        
        Args:
            category: Category name
            item_id: Item ID
            server: Server number
            days: Number of days to look back
            
        Returns:
            List of price history entries
        """
        logger.info(f"Fetching price history for {item_id} in {category} (last {days} days)")
        
        params = {
            "server": server,
            "days": days
        }
        
        data = await self._request(
            "GET",
            f"market/{category}/{item_id}/history",
            params=params
        )
        
        history = data.get("history", [])
        logger.info(f"Successfully fetched {len(history)} price history entries")
        return history