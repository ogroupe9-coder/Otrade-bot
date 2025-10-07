"""
Supabase service for OTRADE Bot database operations (sessions + invoices + conversations)
"""
from supabase import create_client, Client
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from .config import config
from .schemas import InvoiceRecord, ConversationRecord
from .woocommerce_service import woocommerce_service

logger = logging.getLogger(__name__)


class SupabaseService:
    def __init__(self):
        url = getattr(config, "supabase_url", None)
        key = getattr(config, "supabase_key", None)
        if not url or not key:
            logger.warning("Supabase not configured (URL/KEY missing). DB ops will be no-ops.")
            self.client = None
        else:
            self.client: Client = create_client(url, key)

    def _ready(self) -> bool:
        return self.client is not None

    # ----------------- Sessions -----------------
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a session row by ID."""
        if not self._ready():
            return None
        try:
            result = (
                self.client.table("sessions")
                .select("*")
                .eq("session_id", session_id)
                .limit(1)
                .execute()
            )
            rows = result.data or []
            return rows[0] if rows else None
        except Exception as e:
            logger.debug(f"Session {session_id} not found: {e}")
            return None

    async def ensure_session(self, session_id: str, phone_number: Optional[str] = None) -> Dict[str, Any]:
        """Ensure a session row exists, create if not. Preload WooCommerce catalog (lightweight)."""
        session = await self.get_session(session_id)
        if session:
            return session
        try:
            # Preload WooCommerce catalog (name + description only to reduce tokens)
            products = woocommerce_service.list_products(per_page=100)
            catalog = [
                {
                    "name": p.name,
                    "description": getattr(p, "short_description", "") or ""
                }
                for p in products
            ]

            data = {
                "session_id": session_id,
                "phone_number": phone_number,
                "state": {"catalog": catalog},
                "last_activity": datetime.utcnow().isoformat(),
            }
            result = self.client.table("sessions").insert(data).execute()
            if getattr(result, "data", None):
                return result.data[0]
            return data
        except Exception as e:
            logger.error(f"Error creating session {session_id}: {e}")
            return {"session_id": session_id, "state": {}}

    async def update_session_state(self, session_id: str, new_state: Dict[str, Any]) -> bool:
        """Merge with existing state instead of overwriting."""
        if not self._ready():
            return False
        try:
            session = await self.get_session(session_id)
            old_state = session.get("state", {}) if session else {}
            merged = {**old_state, **new_state}
            result = (
                self.client.table("sessions")
                .update({
                    "state": merged,
                    "last_activity": datetime.utcnow().isoformat()
                })
                .eq("session_id", session_id)
                .execute()
            )
            return bool(getattr(result, "data", None))
        except Exception as e:
            logger.error(f"Error updating state for {session_id}: {e}")
            return False

    # ----------------- Conversations -----------------
    async def save_message(self, session_id: str, role: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Save a single conversation message into the DB."""
        if not self._ready():
            return False
        try:
            data = {
                "session_id": session_id,
                "role": role,  # "user" or "assistant"
                "message": message,
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat(),
            }
            result = self.client.table("conversations").insert(data).execute()
            return bool(getattr(result, "data", None))
        except Exception as e:
            logger.error(f"Error saving message for {session_id}: {e}")
            return False

    async def get_recent_messages(self, session_id: str, limit: int = 4) -> List[ConversationRecord]:
        """Retrieve the last N conversation rows for a session (newest → oldest)."""
        if not self._ready():
            return []
        try:
            result = (
                self.client.table("conversations")
                .select("*")
                .eq("session_id", session_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            items = getattr(result, "data", []) or []
            # reverse so it returns oldest → newest
            items = list(reversed(items))
            records: List[ConversationRecord] = []
            for r in items:
                try:
                    records.append(ConversationRecord(**r))
                except Exception as parse_err:
                    logger.warning(f"Conversation record parse issue: {parse_err}")
            return records
        except Exception as e:
            logger.error(f"Error retrieving recent conversation for {session_id}: {e}")
            return []

    async def get_conversation_history(self, session_id: str, limit: int = 20) -> List[ConversationRecord]:
        """Retrieve last N conversation rows for a session (oldest → newest)."""
        if not self._ready():
            return []
        try:
            result = (
                self.client.table("conversations")
                .select("*")
                .eq("session_id", session_id)
                .order("created_at", desc=False)
                .limit(limit)
                .execute()
            )
            items = getattr(result, "data", []) or []
            records: List[ConversationRecord] = []
            for r in items:
                try:
                    records.append(ConversationRecord(**r))
                except Exception as parse_err:
                    logger.warning(f"Conversation record parse issue: {parse_err}")
            return records
        except Exception as e:
            logger.error(f"Error retrieving conversation history for {session_id}: {e}")
            return []

    # ----------------- Invoices -----------------
        # ----------------- Invoices -----------------
    async def upload_pdf(self, file_path: str, file_name: str) -> Optional[str]:
        """Upload PDF file to Supabase Storage (bucket: invoices) and return public URL."""
        if not self._ready():
            return None
        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()

            # ✅ Upload to Supabase Storage (remove "upsert")
            res = self.client.storage.from_("invoices").upload(
                file_name,   # path inside bucket
                file_bytes,  # binary data
                {"content-type": "application/pdf"}
            )

            # If upload fails, res may contain an error
            if isinstance(res, dict) and res.get("error"):
                logger.error(f"Supabase Storage upload error: {res['error']}")
                return None

            # ✅ Always build a public URL for access
            public_url = self.client.storage.from_("invoices").get_public_url(file_name)
            if not public_url:
                logger.error("Failed to retrieve public URL after upload.")
                return None

            logger.info(f"✅ PDF uploaded to Supabase Storage: {public_url}")
            return public_url

        except Exception as e:
            logger.error(f"Error uploading PDF: {e}", exc_info=True)
            return None


    async def save_invoice(self, invoice_record: InvoiceRecord) -> bool:
        """Save invoice record into Supabase table invoices with real public URL."""
        if not self._ready():
            return False
        try:
            if not invoice_record.pdf_url or not invoice_record.pdf_url.startswith("http"):
                logger.error("Invoice has no valid public URL, skipping DB insert.")
                return False

            data = {
                "session_id": invoice_record.session_id,
                "invoice_number": invoice_record.invoice_number,
                "pdf_url": invoice_record.pdf_url,
                "order_data": invoice_record.order_data,
                "total_amount": invoice_record.total_amount,
                "currency": invoice_record.currency,
                "status": invoice_record.status,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
            result = self.client.table("invoices").insert(data).execute()
            return bool(getattr(result, "data", None))
        except Exception as e:
            logger.error(f"Error saving invoice: {e}")
            return False

    async def get_session_invoices(self, session_id: str) -> List[InvoiceRecord]:
        """Retrieve invoices for a given session."""
        if not self._ready():
            return []
        try:
            result = (
                self.client.table("invoices")
                .select("*")
                .eq("session_id", session_id)
                .order("created_at", desc=True)
                .execute()
            )
            items = getattr(result, "data", []) or []
            invoices: List[InvoiceRecord] = []
            for r in items:
                try:
                    invoices.append(InvoiceRecord(**r))
                except Exception as parse_err:
                    logger.warning(f"Invoice record parse issue: {parse_err}")
            return invoices
        except Exception as e:
            logger.error(f"Error retrieving invoices for {session_id}: {e}")
            return []


# Global instance
supabase_service = SupabaseService()
