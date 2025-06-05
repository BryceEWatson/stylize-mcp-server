"""User management service for SaaS customer onboarding."""

import logging
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from google.cloud import firestore
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.models import (
    APIPermission,
    SubscriptionLimits,
    SubscriptionTier,
    UserLoginRequest,
    UserProfile,
    UserRegistrationRequest,
    UserUsageStats,
)

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing user registration, authentication, and subscriptions."""

    def __init__(self):
        """Initialize the user service."""
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.project_id = os.environ.get("GCP_PROJECT_ID")

        if not self.project_id:
            logger.warning("GCP_PROJECT_ID environment variable not set - user service will be limited")

        # JWT configuration
        self.secret_key = os.environ.get("JWT_SECRET_KEY", secrets.token_hex(32))
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60 * 24  # 24 hours

        # Initialize Firestore client
        self.firestore_client = None
        if self.project_id:
            try:
                self.firestore_client = firestore.Client(project=self.project_id)
                # Test connectivity
                self.firestore_client.collection('_test').limit(1).get()
                logger.info("Firestore client initialized and tested successfully for user management")
            except Exception as e:
                logger.error(f"Failed to initialize Firestore client for user service: {str(e)}")
                # Don't fail silently - this is critical for user functionality
                # But allow the service to start for health checks
                self.firestore_client = None

        # Define subscription limits
        self.subscription_limits = {
            SubscriptionTier.FREE: SubscriptionLimits(
                monthly_images=100,
                max_api_keys=1,
                available_styles=["van_gogh", "pixel_art", "flat_ui_icon"],
                priority_support=False,
                custom_styles=False
            ),
            SubscriptionTier.PRO: SubscriptionLimits(
                monthly_images=1000,
                max_api_keys=5,
                available_styles=["van_gogh", "pixel_art", "flat_ui_icon", "neumorphic_button", "abstract_geometric"],
                priority_support=True,
                custom_styles=True
            ),
            SubscriptionTier.ENTERPRISE: SubscriptionLimits(
                monthly_images=10000,
                max_api_keys=999,
                available_styles=["van_gogh", "pixel_art", "flat_ui_icon", "neumorphic_button", "abstract_geometric"],
                priority_support=True,
                custom_styles=True
            )
        }

    def hash_password(self, password: str) -> str:
        """Hash a password for secure storage."""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> dict | None:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None

    async def register_user(self, registration: UserRegistrationRequest) -> tuple[bool, str, UserProfile | None]:
        """Register a new user."""
        try:
            if not self.firestore_client:
                return False, "User registration not available (Firestore not configured)", None

            # Check if user already exists
            users_ref = self.firestore_client.collection('users')
            existing_user = users_ref.where('email', '==', registration.email).limit(1).get()

            if len(existing_user) > 0:
                return False, "User with this email already exists", None

            # Create new user
            user_id = f"user-{uuid.uuid4().hex[:12]}"
            hashed_password = self.hash_password(registration.password)

            user_profile = UserProfile(
                user_id=user_id,
                email=registration.email,
                first_name=registration.first_name,
                last_name=registration.last_name,
                company=registration.company,
                subscription_tier=SubscriptionTier.FREE,
                is_active=True,
                is_email_verified=False,  # TODO: Implement email verification
                created_at=datetime.now(timezone.utc).isoformat()
            )

            # Store in Firestore
            user_doc = {
                **user_profile.dict(),
                "hashed_password": hashed_password
            }

            users_ref.document(user_id).set(user_doc)

            # Initialize usage stats
            usage_stats = UserUsageStats(user_id=user_id)
            self.firestore_client.collection('user_usage').document(user_id).set(usage_stats.dict())

            logger.info(f"Successfully registered new user: {user_id}")
            return True, "User registered successfully", user_profile

        except Exception as e:
            logger.error(f"Error registering user: {str(e)}")
            return False, f"Registration failed: {str(e)}", None

    async def authenticate_user(self, login: UserLoginRequest) -> tuple[bool, str, UserProfile | None]:
        """Authenticate a user login."""
        try:
            if not self.firestore_client:
                return False, "Authentication not available (Firestore not configured)", None

            # Find user by email
            users_ref = self.firestore_client.collection('users')
            user_docs = users_ref.where('email', '==', login.email).limit(1).get()

            if len(user_docs) == 0:
                return False, "Invalid email or password", None

            user_doc = user_docs[0]
            user_data = user_doc.to_dict()

            # Verify password
            if not self.verify_password(login.password, user_data['hashed_password']):
                return False, "Invalid email or password", None

            # Check if user is active
            if not user_data.get('is_active', True):
                return False, "Account is deactivated", None

            # Update last login
            users_ref.document(user_data['user_id']).update({
                'last_login_at': datetime.now(timezone.utc).isoformat()
            })

            # Create user profile (without password)
            user_data.pop('hashed_password', None)
            user_profile = UserProfile(**user_data)

            logger.info(f"Successfully authenticated user: {user_profile.user_id}")
            return True, "Authentication successful", user_profile

        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            return False, f"Authentication failed: {str(e)}", None

    async def get_user_by_id(self, user_id: str) -> UserProfile | None:
        """Get user profile by ID."""
        try:
            if not self.firestore_client:
                return None

            user_doc = self.firestore_client.collection('users').document(user_id).get()
            if not user_doc.exists:
                return None

            user_data = user_doc.to_dict()
            user_data.pop('hashed_password', None)  # Remove password from profile

            return UserProfile(**user_data)

        except Exception as e:
            logger.error(f"Error getting user {user_id}: {str(e)}")
            return None

    def get_subscription_limits(self, tier: SubscriptionTier) -> SubscriptionLimits:
        """Get limits for a subscription tier."""
        return self.subscription_limits.get(tier, self.subscription_limits[SubscriptionTier.FREE])

    async def get_user_usage_stats(self, user_id: str) -> UserUsageStats | None:
        """Get user usage statistics."""
        try:
            if not self.firestore_client:
                return None

            usage_doc = self.firestore_client.collection('user_usage').document(user_id).get()
            if not usage_doc.exists:
                # Create default usage stats
                usage_stats = UserUsageStats(user_id=user_id)
                self.firestore_client.collection('user_usage').document(user_id).set(usage_stats.dict())
                return usage_stats

            return UserUsageStats(**usage_doc.to_dict())

        except Exception as e:
            logger.error(f"Error getting usage stats for user {user_id}: {str(e)}")
            return None

    async def increment_user_usage(self, user_id: str, count: int = 1) -> bool:
        """Increment user's monthly usage count.

        Args:
            user_id: The user's ID
            count: Number of images to increment by (default 1)
        """
        try:
            if not self.firestore_client:
                return False

            # Use a transaction to ensure atomic updates
            @firestore.transactional
            def update_usage(transaction, usage_ref):
                usage_doc = usage_ref.get(transaction=transaction)

                if usage_doc.exists:
                    current_data = usage_doc.to_dict()
                    transaction.update(usage_ref, {
                        'current_month_usage': current_data.get('current_month_usage', 0) + count,
                        'total_usage': current_data.get('total_usage', 0) + count,
                        'last_usage_at': datetime.now(timezone.utc).isoformat()
                    })
                else:
                    # Create new usage record
                    usage_stats = UserUsageStats(
                        user_id=user_id,
                        current_month_usage=count,
                        total_usage=count,
                        last_usage_at=datetime.now(timezone.utc).isoformat()
                    )
                    transaction.set(usage_ref, usage_stats.dict())

            usage_ref = self.firestore_client.collection('user_usage').document(user_id)
            transaction = self.firestore_client.transaction()
            update_usage(transaction, usage_ref)

            return True

        except Exception as e:
            logger.error(f"Error incrementing usage for user {user_id}: {str(e)}")
            return False

    async def check_usage_limits(self, user_id: str, requested_count: int = 1) -> tuple[bool, str]:
        """Check if user has exceeded their usage limits.

        Args:
            user_id: The user's ID
            requested_count: Number of images being requested (default 1)
        """
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return False, "User not found"

            usage_stats = await self.get_user_usage_stats(user_id)
            if not usage_stats:
                return False, "Usage stats not available"

            limits = self.get_subscription_limits(user.subscription_tier)

            if usage_stats.current_month_usage + requested_count > limits.monthly_images:
                remaining = max(0, limits.monthly_images - usage_stats.current_month_usage)
                return False, f"Monthly limit of {limits.monthly_images} images would be exceeded. You have {remaining} images remaining this month."

            return True, "Usage within limits"

        except Exception as e:
            logger.error(f"Error checking usage limits for user {user_id}: {str(e)}")
            return False, "Error checking usage limits"

    async def create_user_api_key(self, user_id: str, name: str) -> tuple[bool, str, str | None]:
        """Create an API key for a user."""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return False, "User not found", None

            # Check API key limits
            limits = self.get_subscription_limits(user.subscription_tier)
            usage_stats = await self.get_user_usage_stats(user_id)

            if usage_stats and usage_stats.api_key_count >= limits.max_api_keys:
                return False, f"API key limit of {limits.max_api_keys} exceeded", None

            # Generate API key with user context
            from app.auth_service import AuthService
            auth_service = AuthService()

            # Create permissions based on subscription tier
            permissions = [APIPermission.STYLIZE, APIPermission.STYLES]
            if user.subscription_tier in [SubscriptionTier.PRO, SubscriptionTier.ENTERPRISE]:
                permissions.append(APIPermission.MCP)

            plain_key, api_key_auth = await auth_service.create_api_key(
                name=f"{user.first_name} {user.last_name} - {name}",
                permissions=permissions
            )

            # Store key association with user
            api_key_auth.user_id = user_id  # Add user_id to the key

            # Update user's API key count
            if usage_stats:
                usage_ref = self.firestore_client.collection('user_usage').document(user_id)
                usage_ref.update({'api_key_count': usage_stats.api_key_count + 1})

            logger.info(f"Created API key for user {user_id}: {api_key_auth.key_id}")
            return True, "API key created successfully", plain_key

        except Exception as e:
            logger.error(f"Error creating API key for user {user_id}: {str(e)}")
            return False, f"Failed to create API key: {str(e)}", None

    async def get_user_credits(self, user_id: str):
        """Get user's credit balance."""
        try:
            if not self.firestore_client:
                return None

            credits_doc = self.firestore_client.collection('user_credits').document(user_id).get()
            if not credits_doc.exists:
                # Create default credit record
                from app.models import UserCredits
                default_credits = UserCredits(user_id=user_id)
                self.firestore_client.collection('user_credits').document(user_id).set(default_credits.dict())
                return default_credits

            from app.models import UserCredits
            return UserCredits(**credits_doc.to_dict())

        except Exception as e:
            logger.error(f"Error getting user credits for {user_id}: {str(e)}")
            return None

    async def purchase_credits(self, user_id: str, package_id: str) -> tuple[bool, str]:
        """Purchase credits for a user (simplified - no actual payment processing)."""
        try:
            if not self.firestore_client:
                return False, "Credit purchase not available (Firestore not configured)"

            # Get trial service to access credit packages
            from app.trial_service import TrialService
            trial_service = TrialService()
            package = trial_service.get_credit_package(package_id)

            if not package:
                return False, f"Invalid package ID: {package_id}"

            # Get current credits
            user_credits = await self.get_user_credits(user_id)
            if not user_credits:
                return False, "Could not retrieve user credit information"

            # Calculate new balances
            total_new_credits = package.credits + package.bonus_credits
            new_balance = user_credits.credits_balance + total_new_credits
            new_total_purchased = user_credits.total_credits_purchased + total_new_credits

            # Update credits using transaction
            @firestore.transactional
            def update_credits(transaction, credits_ref):
                transaction.update(credits_ref, {
                    'credits_balance': new_balance,
                    'total_credits_purchased': new_total_purchased,
                    'last_purchase_at': datetime.now(timezone.utc).isoformat()
                })

            credits_ref = self.firestore_client.collection('user_credits').document(user_id)
            transaction = self.firestore_client.transaction()
            update_credits(transaction, credits_ref)

            logger.info(f"User {user_id} purchased {total_new_credits} credits (package: {package_id})")
            return True, f"Successfully purchased {total_new_credits} credits! New balance: {new_balance}"

        except Exception as e:
            logger.error(f"Error purchasing credits for user {user_id}: {str(e)}")
            return False, f"Credit purchase failed: {str(e)}"
