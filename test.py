from app.whatsapp_service import whatsapp_service
import asyncio

async def test():
    await whatsapp_service.send_message("+923121729411", "Hello from OTRADE Bot!")

asyncio.run(test())