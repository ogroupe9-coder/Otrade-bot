"""
WhatsApp service for OTRADE Bot using Twilio
"""
import logging
from twilio.rest import Client
from .config import config

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.from_number = config.twilio_whatsapp_number
        self.client = None

        try:
            # Prefer API key auth (subaccount case)
            if config.twilio_account_sid and config.twilio_api_key_sid and config.twilio_api_key_secret:
                self.client = Client(
                    config.twilio_api_key_sid,
                    config.twilio_api_key_secret,
                    config.twilio_account_sid,
                )
                logger.info("✅ WhatsApp service initialized with Twilio API Key auth")

            # Fallback: classic SID + Auth Token
            elif config.twilio_account_sid and config.twilio_auth_token:
                self.client = Client(config.twilio_account_sid, config.twilio_auth_token)
                logger.info("✅ WhatsApp service initialized with Twilio SID/Auth Token")

            else:
                logger.warning("⚠️ WhatsApp service not initialized: missing Twilio credentials")

        except Exception as e:
            logger.error(f"❌ Error initializing WhatsApp service: {e}", exc_info=True)

    def extract_phone_number(self, from_number: str) -> str:
        return from_number.replace("whatsapp:", "")

    async def send_message(self, to: str, message: str) -> bool:
        if not self.client:
            logger.warning("⚠️ Cannot send WhatsApp message: Twilio client not initialized")
            return False
        try:
            from_whatsapp = f"whatsapp:{self.from_number}"
            to_whatsapp = f"whatsapp:{to}" if not to.startswith("whatsapp:") else to

            msg = self.client.messages.create(
                from_=from_whatsapp,
                to=to_whatsapp,
                body=message
            )
            logger.info(f"✅ WhatsApp message sent to {to} - SID: {msg.sid}")
            return True
        except Exception as e:
            logger.error(f"❌ Error sending WhatsApp message: {e}", exc_info=True)
            return False

# Singleton instance
whatsapp_service = WhatsAppService()
