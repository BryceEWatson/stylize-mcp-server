"""Authentication service for the Stylize MCP Server."""

import hashlib
import json
import logging
import os
import secrets
from datetime import datetime, timezone
from typing import Any

from google.cloud import secretmanager
from passlib.context import CryptContext

from app.models import APIKeyAuth, APIPermission, AuthConfig

logger = logging.getLogger(__name__)

class AuthService:
    """Service for handling API key authentication and authorization."""

    def __init__(self):
        """Initialize the authentication service."""
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.project_id = os.environ.get("GCP_PROJECT_ID")
        self.secret_client = None

        # Load auth configuration
        self.config = AuthConfig(
            enabled=os.environ.get("AUTH_ENABLED", "true").lower() == "true",
            allow_dev_bypass=os.environ.get("AUTH_DEV_BYPASS", "false").lower() == "true",
            secret_manager_key_path=os.environ.get("API_KEYS_SECRET_PATH", "api-keys")
        )

        logger.info(f"Auth service initialized - enabled: {self.config.enabled}, dev_bypass: {self.config.allow_dev_bypass}")

        # Initialize Secret Manager client if we have a project ID
        if self.project_id:
            try:
                self.secret_client = secretmanager.SecretManagerServiceClient()
                logger.info("Secret Manager client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Secret Manager client: {str(e)}")
        else:
            logger.warning("GCP_PROJECT_ID not set, Secret Manager unavailable")

    def is_auth_enabled(self) -> bool:
        """Check if authentication is enabled."""
        return self.config.enabled

    def should_bypass_auth(self) -> bool:
        """Check if auth should be bypassed (for development)."""
        return self.config.allow_dev_bypass and not self.config.enabled

    def generate_api_key(self) -> str:
        """Generate a new secure API key."""
        # Generate a 32-byte random key and encode as hex
        return secrets.token_hex(32)

    def hash_api_key(self, api_key: str) -> str:
        """Hash an API key for secure storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()

    def verify_api_key(self, plain_key: str, hashed_key: str) -> bool:
        """Verify an API key against its hash."""
        return hashlib.sha256(plain_key.encode()).hexdigest() == hashed_key

    async def load_api_keys(self) -> dict[str, APIKeyAuth]:
        """Load API keys from Secret Manager or environment."""
        api_keys = {}

        # Try to load from Secret Manager first
        if self.secret_client and self.project_id and self.config.secret_manager_key_path:
            try:
                secret_name = f"projects/{self.project_id}/secrets/{self.config.secret_manager_key_path}/versions/latest"
                response = self.secret_client.access_secret_version(request={"name": secret_name})
                secret_data = response.payload.data.decode("UTF-8")

                # Parse JSON data containing API keys
                keys_data = json.loads(secret_data)

                for key_id, key_data in keys_data.items():
                    try:
                        api_key = APIKeyAuth(**key_data)
                        api_keys[key_id] = api_key
                        logger.debug(f"Loaded API key: {key_id}")
                    except Exception as e:
                        logger.error(f"Failed to parse API key {key_id}: {str(e)}")

                logger.info(f"Loaded {len(api_keys)} API keys from Secret Manager")
                return api_keys

            except Exception as e:
                logger.warning(f"Failed to load API keys from Secret Manager: {str(e)}")

        # Fallback: Load from environment variables (for development)
        dev_key = os.environ.get("DEV_API_KEY")
        if dev_key and self.config.allow_dev_bypass:
            logger.warning("Using development API key from environment")
            api_keys["dev-key"] = APIKeyAuth(
                key_id="dev-key",
                name="Development Key",
                hashed_key=self.hash_api_key(dev_key),
                permissions=[APIPermission.STYLIZE, APIPermission.STYLES, APIPermission.MCP, APIPermission.ADMIN],
                created_at=datetime.now(timezone.utc).isoformat()
            )

        return api_keys

    async def validate_api_key(self, api_key: str) -> APIKeyAuth | None:
        """Validate an API key and return the associated auth object."""
        if not api_key:
            return None

        # Load all API keys
        api_keys = await self.load_api_keys()

        # Check each key to find a match
        for key_auth in api_keys.values():
            if not key_auth.is_active:
                continue

            if self.verify_api_key(api_key, key_auth.hashed_key):
                # Update usage statistics
                await self._update_key_usage(key_auth.key_id)
                return key_auth

        return None

    def check_permission(self, api_key_auth: APIKeyAuth, required_permission: APIPermission) -> bool:
        """Check if an API key has the required permission."""
        if not api_key_auth.is_active:
            return False

        # Admin permission grants access to everything
        if APIPermission.ADMIN in api_key_auth.permissions:
            return True

        return required_permission in api_key_auth.permissions

    async def _update_key_usage(self, key_id: str) -> None:
        """Update usage statistics for an API key."""
        # In a production system, this would update the key's last_used_at
        # and usage_count in the persistent storage (Secret Manager or database)
        # For now, we'll just log the usage
        logger.debug(f"API key {key_id} used at {datetime.now(timezone.utc).isoformat()}")

    async def create_api_key(
        self,
        name: str,
        permissions: list[APIPermission] = None
    ) -> tuple[str, APIKeyAuth]:
        """Create a new API key.
        
        Returns:
            Tuple of (plain_api_key, api_key_auth_object)
        """
        if permissions is None:
            permissions = [APIPermission.STYLIZE, APIPermission.STYLES]

        # Generate new key
        plain_key = self.generate_api_key()
        hashed_key = self.hash_api_key(plain_key)
        key_id = f"key-{secrets.token_hex(8)}"

        # Create auth object
        api_key_auth = APIKeyAuth(
            key_id=key_id,
            name=name,
            hashed_key=hashed_key,
            permissions=permissions,
            created_at=datetime.now(timezone.utc).isoformat()
        )

        logger.info(f"Created new API key: {key_id} with permissions: {[p.value for p in permissions]}")

        return plain_key, api_key_auth

    def extract_api_key_from_header(self, authorization: str | None) -> str | None:
        """Extract API key from Authorization header."""
        if not authorization:
            return None

        # Support both "Bearer <key>" and "ApiKey <key>" formats
        if authorization.startswith("Bearer "):
            return authorization[7:]  # Remove "Bearer " prefix
        elif authorization.startswith("ApiKey "):
            return authorization[7:]  # Remove "ApiKey " prefix
        else:
            # Also support plain key without prefix for simplicity
            return authorization

    async def save_api_keys_to_secret_manager(self, api_keys: dict[str, APIKeyAuth]) -> bool:
        """Save API keys to Google Cloud Secret Manager."""
        if not self.secret_client or not self.project_id or not self.config.secret_manager_key_path:
            logger.warning("Cannot save to Secret Manager: client or configuration missing")
            return False

        try:
            # Convert APIKeyAuth objects to dict for JSON serialization
            keys_data = {}
            for key_id, key_auth in api_keys.items():
                keys_data[key_id] = {
                    "key_id": key_auth.key_id,
                    "name": key_auth.name,
                    "hashed_key": key_auth.hashed_key,
                    "is_active": key_auth.is_active,
                    "permissions": [p.value for p in key_auth.permissions],
                    "created_at": key_auth.created_at,
                    "last_used_at": key_auth.last_used_at,
                    "usage_count": key_auth.usage_count
                }

            # Create or update the secret
            secret_data = json.dumps(keys_data, indent=2)
            parent = f"projects/{self.project_id}"
            secret_id = self.config.secret_manager_key_path

            # Try to create a new version of the secret
            try:
                secret_name = f"{parent}/secrets/{secret_id}"
                response = self.secret_client.add_secret_version(
                    request={
                        "parent": secret_name,
                        "payload": {"data": secret_data.encode("UTF-8")},
                    }
                )
                logger.info(f"API keys saved to Secret Manager: {response.name}")
                return True
            except Exception as e:
                # If the secret doesn't exist, create it first
                if "not found" in str(e).lower():
                    try:
                        secret = self.secret_client.create_secret(
                            request={
                                "parent": parent,
                                "secret_id": secret_id,
                                "secret": {"replication": {"automatic": {}}},
                            }
                        )
                        # Now add the first version
                        response = self.secret_client.add_secret_version(
                            request={
                                "parent": secret.name,
                                "payload": {"data": secret_data.encode("UTF-8")},
                            }
                        )
                        logger.info(f"Created new secret and saved API keys: {response.name}")
                        return True
                    except Exception as create_error:
                        logger.error(f"Failed to create secret: {create_error}")
                        return False
                else:
                    raise e

        except Exception as e:
            logger.error(f"Failed to save API keys to Secret Manager: {str(e)}")
            return False

    async def create_and_store_api_key(
        self,
        name: str,
        permissions: list[APIPermission] = None
    ) -> tuple[str, APIKeyAuth]:
        """Create a new API key and store it in Secret Manager."""
        # Create the API key
        plain_key, api_key_auth = await self.create_api_key(name, permissions)

        # Load existing keys
        existing_keys = await self.load_api_keys()

        # Add the new key
        existing_keys[api_key_auth.key_id] = api_key_auth

        # Save back to Secret Manager
        if await self.save_api_keys_to_secret_manager(existing_keys):
            logger.info(f"Successfully created and stored API key: {api_key_auth.key_id}")
        else:
            logger.warning(f"Created API key {api_key_auth.key_id} but failed to persist to Secret Manager")

        return plain_key, api_key_auth

    async def list_api_keys(self) -> list[dict[str, Any]]:
        """List all API keys (without the actual key values)."""
        api_keys = await self.load_api_keys()

        result = []
        for key_auth in api_keys.values():
            result.append({
                "key_id": key_auth.key_id,
                "name": key_auth.name,
                "is_active": key_auth.is_active,
                "permissions": [p.value for p in key_auth.permissions],
                "created_at": key_auth.created_at,
                "last_used_at": key_auth.last_used_at,
                "usage_count": key_auth.usage_count
            })

        return result

    async def deactivate_api_key(self, key_id: str) -> bool:
        """Deactivate an API key."""
        # Load existing keys
        existing_keys = await self.load_api_keys()

        if key_id not in existing_keys:
            logger.warning(f"API key {key_id} not found")
            return False

        # Deactivate the key
        existing_keys[key_id].is_active = False

        # Save back to Secret Manager
        success = await self.save_api_keys_to_secret_manager(existing_keys)
        if success:
            logger.info(f"Successfully deactivated API key: {key_id}")
        else:
            logger.error(f"Failed to persist deactivation of API key: {key_id}")

        return success

    async def update_api_key(self, key_id: str, is_active: bool | None = None, permissions: list[APIPermission] | None = None) -> bool:
        """Update an API key's properties."""
        # Load existing keys
        existing_keys = await self.load_api_keys()

        if key_id not in existing_keys:
            logger.warning(f"API key {key_id} not found")
            return False

        # Update the key
        if is_active is not None:
            existing_keys[key_id].is_active = is_active
        if permissions is not None:
            existing_keys[key_id].permissions = permissions

        # Save back to Secret Manager
        success = await self.save_api_keys_to_secret_manager(existing_keys)
        if success:
            logger.info(f"Successfully updated API key: {key_id}")
        else:
            logger.error(f"Failed to persist update of API key: {key_id}")

        return success
