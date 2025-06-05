"""
E2E API client for testing REST API endpoints.
"""
import httpx
from typing import Optional, Dict, Any, List
import json


class E2EAPIClient:
    """HTTP client for E2E API testing."""
    
    def __init__(self, base_url: str, timeout: int = 60, api_key: Optional[str] = None, jwt_token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.timeout = httpx.Timeout(timeout)
        self.api_key = api_key
        self.jwt_token = jwt_token
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            elif self.jwt_token:
                headers["Authorization"] = f"Bearer {self.jwt_token}"
            
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=headers
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    # Health and basic endpoints
    async def health_check(self) -> httpx.Response:
        """Check application health."""
        return await self.client.get("/health")
    
    # Trial session endpoints
    async def start_trial_session(self) -> httpx.Response:
        """Start a new trial session."""
        return await self.client.post("/trial/start")
    
    async def check_trial_status(self, session_id: str) -> httpx.Response:
        """Check trial session status."""
        return await self.client.get(f"/trial/status?session_id={session_id}")
    
    async def convert_trial_to_user(self, data: Dict[str, Any]) -> httpx.Response:
        """Convert trial session to user account."""
        return await self.client.post("/trial/convert", json=data)
    
    # Image generation endpoints
    async def stylize_image(
        self,
        image_data: bytes,
        style_id: Optional[str] = None,
        user_prompt: Optional[str] = None,
        session_id: Optional[str] = None,
        project_context: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        """Generate stylized image."""
        files = {"image": ("test_image.jpg", image_data, "image/jpeg")}
        data = {}
        
        if style_id:
            data["style_id"] = style_id
        if user_prompt:
            data["user_prompt"] = user_prompt
        if session_id:
            data["session_id"] = session_id
        if project_context:
            data["project_context"] = json.dumps(project_context)
        
        return await self.client.post("/stylize_image", files=files, data=data)
    
    async def generate_image_from_text(
        self,
        prompt: str,
        style_id: str,
        session_id: Optional[str] = None,
        project_context: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        """Generate image from text prompt."""
        data = {
            "prompt": prompt,
            "style_id": style_id
        }
        
        if session_id:
            data["session_id"] = session_id
        if project_context:
            data["project_context"] = project_context
        
        return await self.client.post("/generate_image_from_text", json=data)
    
    # Style management endpoints
    async def list_styles(self) -> httpx.Response:
        """List available styles."""
        return await self.client.get("/styles")
    
    async def get_style_details(self, style_id: str) -> httpx.Response:
        """Get details for a specific style."""
        return await self.client.get(f"/styles/{style_id}")
    
    # User management endpoints
    async def register_user(self, user_data: Dict[str, Any]) -> httpx.Response:
        """Register a new user."""
        return await self.client.post("/auth/register", json=user_data)
    
    async def login_user(self, email: str, password: str) -> httpx.Response:
        """Login user."""
        data = {"username": email, "password": password}
        return await self.client.post("/auth/login", data=data)
    
    async def get_user_profile(self) -> httpx.Response:
        """Get user profile (requires authentication)."""
        return await self.client.get("/user/profile")
    
    async def get_user_credits(self) -> httpx.Response:
        """Get user credit balance (requires authentication)."""
        return await self.client.get("/user/credits")
    
    async def get_user_dashboard(self) -> httpx.Response:
        """Get user dashboard data (requires authentication)."""
        return await self.client.get("/user/dashboard")
    
    # Credit management endpoints
    async def purchase_credits(self, package_id: str) -> httpx.Response:
        """Purchase credit package (requires authentication)."""
        return await self.client.post("/user/purchase-credits", json={"package_id": package_id})
    
    async def get_pricing_packages(self) -> httpx.Response:
        """Get available pricing packages."""
        return await self.client.get("/pricing/packages")
    
    # Web interface endpoints
    async def get_web_demo(self) -> httpx.Response:
        """Get demo page."""
        return await self.client.get("/web/demo")
    
    async def get_web_upgrade(self) -> httpx.Response:
        """Get trial upgrade page."""
        return await self.client.get("/web/upgrade")
    
    async def get_web_dashboard(self) -> httpx.Response:
        """Get user dashboard page."""
        return await self.client.get("/web/dashboard")
    
    async def post_web_trial_upgrade(self, form_data: Dict[str, Any]) -> httpx.Response:
        """Submit trial upgrade form."""
        return await self.client.post("/web/trial/upgrade", data=form_data)
    
    async def post_web_purchase(self, form_data: Dict[str, Any]) -> httpx.Response:
        """Submit credit purchase form."""
        return await self.client.post("/web/purchase", data=form_data)
    
    # Admin endpoints (if testing with admin permissions)
    async def create_api_key(self, name: str, permissions: List[str]) -> httpx.Response:
        """Create API key (requires admin permission)."""
        data = {"name": name, "permissions": permissions}
        return await self.client.post("/admin/api-keys", json=data)
    
    async def list_api_keys(self) -> httpx.Response:
        """List API keys (requires admin permission)."""
        return await self.client.get("/admin/api-keys")
    
    async def deactivate_api_key(self, key_id: str) -> httpx.Response:
        """Deactivate API key (requires admin permission)."""
        return await self.client.delete(f"/admin/api-keys/{key_id}")
    
    # Utility methods for testing
    async def wait_for_service_ready(self, max_attempts: int = 30, delay: float = 1.0) -> bool:
        """Wait for service to be ready."""
        import asyncio
        
        for attempt in range(max_attempts):
            try:
                response = await self.health_check()
                if response.status_code == 200:
                    return True
            except Exception:
                pass
            
            if attempt < max_attempts - 1:
                await asyncio.sleep(delay)
        
        return False
    
    async def upload_file(self, file_path: str, endpoint: str, field_name: str = "file") -> httpx.Response:
        """Upload file to specified endpoint."""
        with open(file_path, "rb") as f:
            files = {field_name: f}
            return await self.client.post(endpoint, files=files)
    
    def set_auth_token(self, token: str, token_type: str = "Bearer"):
        """Set authentication token."""
        if self._client:
            self._client.headers["Authorization"] = f"{token_type} {token}"
        
        if token_type == "Bearer" and not token.startswith("sk-"):  # JWT token
            self.jwt_token = token
        else:  # API key
            self.api_key = token
    
    def clear_auth(self):
        """Clear authentication."""
        if self._client and "Authorization" in self._client.headers:
            del self._client.headers["Authorization"]
        self.api_key = None
        self.jwt_token = None