"""
OpenAI GPT service for OTRADE Bot (state-based, GPT-first approach, with catalog + short history)
"""
import json
import logging
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
from openai import OpenAI

from .config import config
from .schemas import GPTResponse, GPTMetadata
from .supabase_service import supabase_service

logger = logging.getLogger(__name__)


class GPTService:
    def __init__(self):
        # Initialize OpenAI client
        self.client = OpenAI(api_key=getattr(config, "openai_api_key", None))
        self.model = getattr(config, "openai_model", None) or "gpt-4o"
        self.temperature = getattr(config, "openai_temperature", 0.3)
        self.governor_prompt = self._load_governor_prompt()

        # Token safety defaults
        self.max_tokens = 800
        self.max_catalog_items = 50     # limit number of products passed to GPT
        self.max_state_keys = 12        # avoid dumping huge states
        self.history_turns = 10         # number of past user/assistant messages to include (increased for better context)

    def _load_governor_prompt(self) -> str:
        """Load governor prompt from file or fallback."""
        try:
            base = Path(__file__).resolve().parent.parent
            for name in ["governor_prompt.txt", "governer_prompt.txt"]:
                p = base / name
                if p.exists():
                    text = p.read_text(encoding="utf-8").strip()
                    if text:
                        logger.info(f"Loaded governor prompt from {p.name}")
                        return text
            logger.warning("Governor prompt missing, using fallback.")
            return "You are OTRADE sales advisor. Help customers with wholesale trading."
        except Exception as e:
            logger.error(f"Error loading governor prompt: {str(e)}")
            return "You are OTRADE sales advisor. Help customers with wholesale trading."

    def _build_context_reminder(self, state: Dict[str, Any]) -> str:
        """Build a human-readable summary of what's been collected to prevent re-asking."""
        
        collected = []
        missing = []
        
        # Required fields for PDF generation
        required_fields = {
            "product_name": "Product",
            "quantity": "Quantity",
            "quantity_unit": "Unit (carton/pallet/container)",
            "destination_country": "Destination Country",
            "city": "City",
            "street_address": "Street Address",
            "shipping_incoterm": "Shipping Term (FOB/CIF)",
            "payment_option": "Payment Option"
        }
        
        for key, label in required_fields.items():
            value = state.get(key)
            if value:
                collected.append(f"✓ {label}: {value}")
            else:
                missing.append(f"✗ {label}: NOT YET PROVIDED")
        
        summary = "═══════════════════════════════════════\n"
        summary += "   ORDER INFORMATION TRACKING\n"
        summary += "═══════════════════════════════════════\n\n"
        
        if collected:
            summary += "✅ CONFIRMED DETAILS (NEVER ask for these again!):\n"
            summary += "\n".join(f"   {item}" for item in collected) + "\n\n"
        
        if missing:
            summary += "❌ STILL NEEDED (ask ONLY for these missing fields):\n"
            summary += "\n".join(f"   {item}" for item in missing) + "\n\n"
        
        summary += "⚠️ CRITICAL RULES:\n"
        summary += "   1. If a field is marked with ✓ above, it is CONFIRMED and PERMANENT\n"
        summary += "   2. NEVER ask for confirmed fields again\n"
        summary += "   3. NEVER set confirmed fields to null in your JSON response\n"
        summary += "   4. ONLY ask for fields marked with ✗\n"
        summary += "   5. In your JSON output, include ALL confirmed fields with their current values\n"
        summary += "═══════════════════════════════════════\n"
        
        return summary


    async def process_message(self, session_id: str, user_message: str) -> GPTResponse:
        """
        Main entry:
        - Load session state + conversation history from Supabase
        - Pass governor prompt, catalog subset, state, history, and new user message to GPT
        - Parse GPT response into natural reply + structured metadata
        """
        try:
            # Load current session state
            session = await supabase_service.ensure_session(session_id)
            state_json = session.get("state", {}) if session else {}

            # Extract catalog subset (to reduce tokens)
            catalog = state_json.get("catalog", [])
            catalog_trimmed = catalog[: self.max_catalog_items] if catalog else []

            # Trim state (exclude large fields)
            safe_state = {
                k: v for k, v in state_json.items()
                if k not in ("catalog", "product_choice_pending")
            }
            if len(safe_state) > self.max_state_keys:
                safe_state = dict(list(safe_state.items())[:self.max_state_keys])

            # Load recent conversation history
            history = await supabase_service.get_conversation_history(
                session_id, limit=self.history_turns * 2
            )
            history_messages: List[Dict[str, str]] = []
            for h in history[-self.history_turns * 2:]:
                if h.role == "user":
                    history_messages.append({"role": "user", "content": h.message})
                else:
                    history_messages.append({"role": "assistant", "content": h.message})

            # Strict system instructions
            system_instruction = (
                "You must output TWO parts:\n"
                "1. A natural, human response (multi-line allowed).\n"
                "2. On the FINAL line only, output a single JSON object representing the UPDATED STATE.\n"
                "Never wrap JSON in code fences. Never add text after it.\n\n"
                "The JSON schema is exactly:\n"
                "{\n"
                '  "category": "Products & Sourcing" | "Logistics & Shipping" | "Payments & Finance" | "Guarantees & Quality" | "Relationship & Psychology",\n'
                '  "ready_for_pdf": boolean,\n'
                '  "product_name": string | null,\n'
                '  "quantity": number | null,\n'
                '  "quantity_unit": string | null,\n'  
                '  "destination_country": string | null,\n'
                '  "city": string | null,\n'
                '  "street_address": string | null,\n'
                '  "shipping_incoterm": "FOB" | "CIF" | null,\n'
                '  "payment_option": string | null\n'
                "}\n\n"
                "Rules:\n"
                "..."
            )



            # Build context reminder showing what's confirmed vs missing
            context_reminder = self._build_context_reminder(safe_state)

            # Build GPT messages
            messages: List[Dict[str, str]] = [
                {"role": "system", "content": system_instruction},
                {"role": "system", "content": context_reminder},  # NEW: explicit context tracking
                {"role": "system", "content": self.governor_prompt},
                {"role": "system", "content": f"Current session state: {json.dumps(safe_state)}"},
            ]
            if catalog_trimmed:
                messages.append(
                    {"role": "system", "content": f"Product catalog (subset): {json.dumps(catalog_trimmed)}"}
                )

            # Add recent conversation history
            messages.extend(history_messages)

            # Add the latest user message
            messages.append({"role": "user", "content": user_message})

            # Call OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            full_response = (response.choices[0].message.content or "").strip()
            natural_response, metadata_dict = self._parse_response(full_response)

            # Parse JSON into GPTMetadata
            try:
                metadata = GPTMetadata(**metadata_dict)
            except Exception as e:
                logger.warning(f"Failed to cast metadata: {e}; using defaults.")
                metadata = GPTMetadata(
                    category="Relationship & Psychology",
                    product_name=None,
                    quantity=None,
                    destination_country=None,
                    city=None,
                    street_address=None,
                    shipping_incoterm=None,
                    payment_option=None,
                    ready_for_pdf=False,
                )

            return GPTResponse(natural_response=natural_response, metadata=metadata)

        except Exception as e:
            logger.error(f"Error processing GPT message: {str(e)}", exc_info=True)
            return GPTResponse(
                natural_response="I’m sorry — something went wrong. Could you please try again?",
                metadata=GPTMetadata(
                    category="Relationship & Psychology",
                    product_name=None,
                    quantity=None,
                    destination_country=None,
                    city=None,
                    street_address=None,
                    shipping_incoterm=None,
                    payment_option=None,
                    ready_for_pdf=False,
                ),
            )

    def _parse_response(self, full_response: str) -> Tuple[str, Dict[str, Any]]:
        """Split natural reply from JSON state."""
        default_metadata = {
            "category": "Relationship & Psychology",
            "ready_for_pdf": False,
            "product_name": None,
            "quantity": None,
            "destination_country": None,
            "city": None,
            "street_address": None,
            "shipping_incoterm": None,
            "payment_option": None,
        }

        if not full_response:
            return "", default_metadata

        lines = [l for l in full_response.splitlines() if l.strip()]
        last_line = lines[-1] if lines else ""

        # JSON expected on last line
        if last_line.startswith("{") and last_line.endswith("}"):
            metadata = self._safe_json_load(last_line, default_metadata)
            natural = "\n".join(lines[:-1]).strip()
            return natural, metadata

        # Fallback: try to find last JSON block
        try:
            last_open = full_response.rfind("{")
            last_close = full_response.rfind("}")
            if last_open > -1 and last_close > last_open:
                json_str = full_response[last_open:last_close + 1]
                natural = full_response[:last_open].strip()
                metadata = self._safe_json_load(json_str, default_metadata)
                return natural, metadata
        except Exception as e:
            logger.debug(f"Parse fallback failed: {e}")

        return full_response, default_metadata

    def _safe_json_load(self, s: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
        """Try to load JSON safely."""
        try:
            return json.loads(s)
        except Exception:
            try:
                s2 = s.replace("'", '"')
                return json.loads(s2)
            except Exception as e:
                logger.warning(f"JSON decode error: {e}; fallback.")
                return dict(fallback)


# Global instance
gpt_service = GPTService()
