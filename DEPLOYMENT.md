# Deployment Guide for OTRADE Bot

## Deploying on Render

### Setup

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Configure the following settings:
   - **Name**: otrade-bot
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python run_bot.py`

### Environment Variables

Set the following environment variables in the Render dashboard:

- `OPENAI_API_KEY`: Your OpenAI API key
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase API key
- `TWILIO_ACCOUNT_SID`: Your Twilio account SID
- `TWILIO_AUTH_TOKEN`: Your Twilio auth token
- `TWILIO_PHONE_NUMBER`: Your Twilio phone number (without the "whatsapp:" prefix)

### Twilio WhatsApp Integration

1. In the Twilio console, navigate to the WhatsApp sandbox settings
2. Set the webhook URL to: `https://<your-render-url>/webhook/whatsapp`
3. Make sure the HTTP method is set to POST

### Testing

After deployment, you can test the API with:

- Health check: `GET https://<your-render-url>/health`
- Chat endpoint: `POST https://<your-render-url>/chat` with JSON body:
  ```json
  {
    "session_id": "test123",
    "message": "Do you have vodka?"
  }
  ```
