import os
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("uvicorn")

# Optional import so the app doesn't crash if the library isn't installed yet
# but we will recommend installing it in the requirements.
try:
    # pyrefly: ignore [missing-import]
    import firebase_admin
    # pyrefly: ignore [missing-import]
    from firebase_admin import credentials, messaging
    HAS_FIREBASE = True
except ImportError:
    HAS_FIREBASE = False
    logger.warning(" firebase-admin is not installed. All Firebase notifications will be mocked.")

class FirebaseNotificationService:
    _initialized = False

    @classmethod
    def initialize(cls):
        """Initializes the Firebase Admin SDK securely."""
        if cls._initialized:
            return

        if not HAS_FIREBASE:
            return

        json_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
        
        # 1. First, check if the env variable itself is a raw JSON string
        if json_path and json_path.strip().startswith("{"):
            try:
                cred_dict = json.loads(json_path)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                cls._initialized = True
                logger.info("🔥 Firebase Admin SDK initialized successfully from Raw JSON String!")
                return
            except Exception as e:
                logger.error(f"❌ Failed to parse raw Firebase JSON from environment: {e}")
                return

        # 2. Fall back to treating it as a file path
        if not json_path:
            if os.path.exists("firebase-adminsdk.json"):
                json_path = "firebase-adminsdk.json"
            elif os.path.exists("firebase_adminsdk.json"):
                json_path = "firebase_adminsdk.json"

        if not json_path or not os.path.exists(json_path):
            logger.warning(
                "⚠️ Firebase Service Account JSON not found! "
                "Push notifications will be mocked (logged to console)."
            )
            return

        try:
            cred = credentials.Certificate(json_path)
            firebase_admin.initialize_app(cred)
            cls._initialized = True
            logger.info("🔥 Firebase Admin SDK initialized successfully from file path!")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Firebase Admin SDK: {e}")

    @classmethod
    def send_push_notification(
        cls, 
        token: str, 
        title: str, 
        body: str, 
        data: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Sends a single push notification to a registered device token.
        Supports both background notification fields and custom payloads (data).
        """
        if not cls._initialized or not HAS_FIREBASE:
            logger.info(
                f"[MOCK NOTIFICATION] To Token: {token[:15]}... | "
                f"Title: {title} | Body: {body} | Data: {data}"
            )
            return True # Pretend it worked for local dev ease

        try:
            # Convert all data dictionary values to strings as required by FCM
            fcm_data = {}
            if data:
                for k, v in data.items():
                    fcm_data[str(k)] = str(v)

            # 1. Define visual notification structure
            notification = messaging.Notification(
                title=title,
                body=body
            )

            # 2. Package the complete FCM message
            message = messaging.Message(
                notification=notification,
                data=fcm_data,
                token=token
            )

            # 3. Fire-and-forget request to Firebase
            response = messaging.send(message)
            logger.info(f"🚀 Push notification sent successfully! Message ID: {response}")
            return True
        except Exception as e:
            logger.error(f"FCM Delivery Failure: {e}")
            return False

# Self-initialize on module load
FirebaseNotificationService.initialize()
