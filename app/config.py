"""
Configuration settings for OTRADE Bot
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    def __init__(self):
        # OpenAI
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.openai_temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))

        # Supabase
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")

        # WooCommerce
        self.woocommerce_url = os.getenv("WOOCOMMERCE_URL")
        self.woocommerce_consumer_key = os.getenv("WOOCOMMERCE_CONSUMER_KEY")
        self.woocommerce_consumer_secret = os.getenv("WOOCOMMERCE_CONSUMER_SECRET")

        # Twilio (support both classic and API key auth)
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")  # optional
        self.twilio_api_key_sid = os.getenv("TWILIO_API_KEY_SID")
        self.twilio_api_key_secret = os.getenv("TWILIO_API_KEY_SECRET")
        self.twilio_whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")

        # Bot
        self.max_history_messages = 20
        self.pdf_storage_path = "invoices/"

        # Legacy attribute for compatibility
        self.MAX_HISTORY_MESSAGES = self.max_history_messages

    def validate_required_keys(self) -> bool:
        required = [self.openai_api_key, self.supabase_url, self.supabase_key]
        return all(required)

config = Config()
