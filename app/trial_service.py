"""Trial service for managing anonymous user sessions and freemium experience."""

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone

from google.cloud import firestore

from app.models import (
    CreditPackage,
    MCPTrialResponse,
    TrialSession,
    TrialToAccountRequest,
    TrialUsageResponse,
)

logger = logging.getLogger(__name__)


class TrialService:
    """Service for managing anonymous trial sessions and credit-based billing."""

    def __init__(self):
        """Initialize the trial service."""
        self.project_id = os.environ.get("GCP_PROJECT_ID")
        self.firestore_client = None

        # Trial configuration
        self.trial_images_limit = 5  # Anonymous users get 5 free images
        self.trial_duration_hours = 24  # Trial expires after 24 hours

        # Initialize Firestore client
        if self.project_id:
            try:
                self.firestore_client = firestore.Client(project=self.project_id)
                logger.info("Firestore client initialized for trial management")
            except Exception as e:
                logger.warning(f"Failed to initialize Firestore client: {str(e)}")

        # Define credit packages
        self.credit_packages = {
            "starter": CreditPackage(
                package_id="starter",
                name="Starter Pack",
                credits=50,
                price_usd=9.99,
                bonus_credits=5,
                popular=False
            ),
            "popular": CreditPackage(
                package_id="popular",
                name="Popular Pack",
                credits=200,
                price_usd=29.99,
                bonus_credits=25,
                popular=True
            ),
            "pro": CreditPackage(
                package_id="pro",
                name="Pro Pack",
                credits=500,
                price_usd=59.99,
                bonus_credits=75,
                popular=False
            ),
            "enterprise": CreditPackage(
                package_id="enterprise",
                name="Enterprise Pack",
                credits=1000,
                price_usd=99.99,
                bonus_credits=200,
                popular=False
            )
        }

    def create_session_id(self, ip_address: str, user_agent: str | None = None) -> str:
        """Create a unique session ID based on IP and user agent."""
        # Use IP + timestamp for uniqueness
        base_string = f"{ip_address}-{datetime.now(timezone.utc).isoformat()}"
        return f"trial-{uuid.uuid5(uuid.NAMESPACE_DNS, base_string).hex[:12]}"

    async def get_or_create_trial_session(
        self,
        ip_address: str,
        user_agent: str | None = None
    ) -> TrialSession:
        """Get existing trial session or create a new one."""
        try:
            if not self.firestore_client:
                # Fallback to in-memory session for development
                session_id = self.create_session_id(ip_address, user_agent)
                return TrialSession(
                    session_id=session_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    images_used=0,
                    max_images=self.trial_images_limit,
                    created_at=datetime.now(timezone.utc).isoformat()
                )

            # Look for existing active trial session for this IP
            trials_ref = self.firestore_client.collection('trial_sessions')
            existing_trials = trials_ref.where('ip_address', '==', ip_address).where('is_expired', '==', False).limit(1).get()

            if len(existing_trials) > 0:
                trial_doc = existing_trials[0]
                trial_data = trial_doc.to_dict()

                # Check if trial has expired by time
                created_at = datetime.fromisoformat(trial_data['created_at'].replace('Z', '+00:00'))
                if datetime.now(timezone.utc) - created_at > timedelta(hours=self.trial_duration_hours):
                    # Mark as expired
                    trials_ref.document(trial_doc.id).update({'is_expired': True})
                    # Create new trial session
                    return await self._create_new_trial_session(ip_address, user_agent)

                return TrialSession(**trial_data)

            # Create new trial session
            return await self._create_new_trial_session(ip_address, user_agent)

        except Exception as e:
            logger.error(f"Error getting/creating trial session: {str(e)}")
            # Return fallback session
            session_id = self.create_session_id(ip_address, user_agent)
            return TrialSession(
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                images_used=0,
                max_images=self.trial_images_limit,
                created_at=datetime.now(timezone.utc).isoformat()
            )

    async def _create_new_trial_session(self, ip_address: str, user_agent: str | None = None) -> TrialSession:
        """Create a new trial session."""
        session_id = self.create_session_id(ip_address, user_agent)

        trial_session = TrialSession(
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            images_used=0,
            max_images=self.trial_images_limit,
            created_at=datetime.now(timezone.utc).isoformat()
        )

        if self.firestore_client:
            # Store in Firestore
            trials_ref = self.firestore_client.collection('trial_sessions')
            trials_ref.document(session_id).set(trial_session.dict())

        logger.info(f"Created new trial session: {session_id}")
        return trial_session

    async def check_trial_usage(self, session_id: str, requested_count: int = 1) -> tuple[bool, TrialUsageResponse]:
        """Check if trial session can be used for another image(s).
        
        Args:
            session_id: Trial session ID
            requested_count: Number of images being requested (default 1)
        """
        try:
            if not self.firestore_client:
                # Fallback for development
                return True, TrialUsageResponse(
                    session_id=session_id,
                    images_used=0,
                    images_remaining=self.trial_images_limit,
                    trial_expired=False
                )

            # Get trial session
            trial_doc = self.firestore_client.collection('trial_sessions').document(session_id).get()

            if not trial_doc.exists:
                return False, TrialUsageResponse(
                    session_id=session_id,
                    images_used=0,
                    images_remaining=0,
                    trial_expired=True,
                    upgrade_message="Trial session not found. Please start a new trial.",
                    signup_url="/auth/register"
                )

            trial_data = trial_doc.to_dict()
            trial_session = TrialSession(**trial_data)

            # Check if expired
            if trial_session.is_expired:
                return False, self._create_expired_response(trial_session)

            # Check usage limit (accounting for requested count)
            if trial_session.images_used + requested_count > trial_session.max_images:
                return False, self._create_limit_exceeded_response(trial_session, requested_count)

            # Trial can be used
            images_remaining = trial_session.max_images - trial_session.images_used

            return True, TrialUsageResponse(
                session_id=session_id,
                images_used=trial_session.images_used,
                images_remaining=images_remaining,
                trial_expired=False
            )

        except Exception as e:
            logger.error(f"Error checking trial usage for session {session_id}: {str(e)}")
            return False, TrialUsageResponse(
                session_id=session_id,
                images_used=0,
                images_remaining=0,
                trial_expired=True,
                upgrade_message="Error checking trial status. Please try again.",
                signup_url="/auth/register"
            )

    async def increment_trial_usage(self, session_id: str, count: int = 1) -> bool:
        """Increment trial usage count.
        
        Args:
            session_id: Trial session ID
            count: Number of images to increment by (default 1)
        """
        try:
            if not self.firestore_client:
                # Development fallback
                return True

            # Use a transaction to ensure atomic updates
            @firestore.transactional
            def update_usage(transaction, trial_ref):
                trial_doc = trial_ref.get(transaction=transaction)

                if trial_doc.exists:
                    current_data = trial_doc.to_dict()
                    new_usage = current_data.get('images_used', 0) + count

                    transaction.update(trial_ref, {
                        'images_used': new_usage,
                        'last_used_at': datetime.now(timezone.utc).isoformat()
                    })
                    return True
                return False

            trial_ref = self.firestore_client.collection('trial_sessions').document(session_id)
            transaction = self.firestore_client.transaction()
            return update_usage(transaction, trial_ref)

        except Exception as e:
            logger.error(f"Error incrementing trial usage for session {session_id}: {str(e)}")
            return False

    def _create_expired_response(self, trial_session: TrialSession) -> TrialUsageResponse:
        """Create response for expired trial."""
        return TrialUsageResponse(
            session_id=trial_session.session_id,
            images_used=trial_session.images_used,
            images_remaining=0,
            trial_expired=True,
            upgrade_message=f"Your {self.trial_duration_hours}-hour trial has expired. Sign up for 100 free images per month!",
            signup_url="/auth/register"
        )

    def _create_limit_exceeded_response(self, trial_session: TrialSession, requested_count: int = 1) -> TrialUsageResponse:
        """Create response for trial limit exceeded."""
        images_remaining = max(0, trial_session.max_images - trial_session.images_used)

        if requested_count > 1 and images_remaining > 0:
            upgrade_message = f"You have {images_remaining} trial images remaining, but you requested {requested_count} images. Sign up for 100 free images per month!"
        else:
            upgrade_message = f"You've used all {self.trial_images_limit} trial images! Sign up for 100 free images per month."

        return TrialUsageResponse(
            session_id=trial_session.session_id,
            images_used=trial_session.images_used,
            images_remaining=images_remaining,
            trial_expired=True,
            upgrade_message=upgrade_message,
            signup_url="/auth/register"
        )

    def get_credit_packages(self) -> list[CreditPackage]:
        """Get available credit packages."""
        return list(self.credit_packages.values())

    def get_credit_package(self, package_id: str) -> CreditPackage | None:
        """Get a specific credit package."""
        return self.credit_packages.get(package_id)

    async def convert_trial_to_account(
        self,
        conversion_request: TrialToAccountRequest
    ) -> tuple[bool, str, str | None]:
        """Convert a trial session to a full user account."""
        try:
            # Import here to avoid circular imports
            from app.models import UserRegistrationRequest
            from app.user_service import UserService

            user_service = UserService()

            # Create user account
            registration = UserRegistrationRequest(
                email=conversion_request.email,
                password=conversion_request.password,
                first_name=conversion_request.first_name,
                last_name=conversion_request.last_name,
                company=conversion_request.company
            )

            success, message, user_profile = await user_service.register_user(registration)

            if not success:
                return False, message, None

            # Mark trial session as converted
            if self.firestore_client:
                trial_ref = self.firestore_client.collection('trial_sessions').document(conversion_request.session_id)
                trial_ref.update({
                    'converted_to_user_id': user_profile.user_id,
                    'is_expired': True
                })

            # Create access token
            access_token = user_service.create_access_token(
                data={"sub": user_profile.user_id}
            )

            logger.info(f"Successfully converted trial {conversion_request.session_id} to user {user_profile.user_id}")
            return True, "Account created successfully!", access_token

        except Exception as e:
            logger.error(f"Error converting trial to account: {str(e)}")
            return False, f"Conversion failed: {str(e)}", None

    async def create_mcp_trial_response(
        self,
        success: bool,
        image_url: str | None,
        session_id: str,
        include_upgrade_options: bool = False
    ) -> MCPTrialResponse:
        """Create MCP-compatible trial response."""
        # Get current trial status
        can_use, trial_info = await self.check_trial_usage(session_id)

        # Include upgrade options if trial is expired or requested
        upgrade_options = None
        if include_upgrade_options or trial_info.trial_expired:
            upgrade_options = self.get_credit_packages()

        return MCPTrialResponse(
            success=success,
            image_url=image_url,
            trial_info=trial_info,
            upgrade_options=upgrade_options
        )
