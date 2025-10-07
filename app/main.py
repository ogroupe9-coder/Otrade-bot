"""
FastAPI main application for OTRADE Bot
"""
import logging
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

from .schemas import ChatRequest, ChatResponse
from .router import router
from .whatsapp_service import whatsapp_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OTRADE Bot",
    description="AI-powered wholesale trading assistant for OTRADE",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "OTRADE Bot API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint for testing"""
    try:
        return await router.process_request(request)
    except Exception as e:
        logger.error(f"❌ Chat endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """Webhook endpoint for Twilio WhatsApp messages"""
    try:
        form_data = await request.form()
        from_number = form_data.get("From", "")
        message_body = form_data.get("Body", "")

        logger.info(f"📩 Incoming WhatsApp from {from_number}: {message_body}")

        clean_phone = whatsapp_service.extract_phone_number(from_number)
        session_id = f"whatsapp_{clean_phone}"

        chat_request = ChatRequest(
            session_id=session_id,
            message=message_body,
            phone_number=clean_phone
        )
        result = await router.process_request(chat_request)

        # Reply back to the same user
        success = await whatsapp_service.send_message(clean_phone, result.response)
        if success:
            logger.info(f"✅ WhatsApp reply sent to {clean_phone}")
        else:
            logger.warning(f"⚠️ Failed to send WhatsApp reply to {clean_phone}")

        return Response(content="", status_code=200)

    except Exception as e:
        logger.error(f"❌ WhatsApp webhook error: {e}", exc_info=True)
        return Response(content="", status_code=500)
