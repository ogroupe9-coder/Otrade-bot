"""
CLI testing tool for OTRADE Bot (local debugging)
"""
import asyncio
import uuid
import json
from app.router import router
from app.schemas import ChatRequest
from app.supabase_service import supabase_service


async def cli_loop():
    print("============================================================")
    print("🤖 OTRADE Bot CLI Testing Interface (Standalone)")
    print("============================================================")
    print("Type 'quit' or 'exit' to stop")
    print("------------------------------------------------------------")

    # 🔑 Unique session id for each run
    session_id = f"cli_{uuid.uuid4().hex[:8]}"
    print(f"[Session ID: {session_id}]")

    # ⚡ Ensure session + preload catalog
    session = await supabase_service.ensure_session(session_id, phone_number="cli")
    if session and "catalog" in session.get("state", {}):
        print(f"📦 Catalog preloaded with {len(session['state']['catalog'])} products.")

    while True:
        msg = input("👤 You: ").strip()
        if msg.lower() in {"quit", "exit"}:
            print("👋 Goodbye! Thanks for testing OTRADE Bot.")
            break

        request = ChatRequest(session_id=session_id, message=msg, phone_number="cli")
        response = await router.process_request(request)

        # Print bot reply
        print(f"\n🤖 OTRADE Bot: {response.response}\n")

        # Print metadata for debugging
        print("🗂️ Metadata (session state):")
        try:
            pretty_meta = json.dumps(response.metadata, indent=2)
            print(pretty_meta)
        except Exception:
            print(response.metadata)
        print("-" * 60)


if __name__ == "__main__":
    asyncio.run(cli_loop())
