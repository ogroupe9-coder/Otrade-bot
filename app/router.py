"""
Request router for OTRADE Bot - GPT-first routing and state handling
"""
import logging
from typing import Dict, Any, Optional

from .schemas import ChatRequest, ChatResponse, OrderData, GPTMetadata
from .gpt_service import gpt_service
from .woocommerce_service import woocommerce_service
from .pdf_service import pdf_service
from .supabase_service import supabase_service
from .whatsapp_service import whatsapp_service

logger = logging.getLogger(__name__)


class Router:
    async def process_request(self, request: ChatRequest) -> ChatResponse:
        try:
            # 📝 Log user message (same as before)
            await supabase_service.save_message(
                session_id=request.session_id,
                role="user",
                message=request.message,
                metadata={}
            )

            # 1) Ask GPT
            gpt_response = await gpt_service.process_message(
                request.session_id, request.message
            )

            metadata: Optional[GPTMetadata] = gpt_response.metadata
            category = metadata.category if metadata else "Relationship & Psychology"
            ready_for_pdf = metadata.ready_for_pdf if metadata else False

            # 2) Load current session state (same call signature as older version)
            session = await supabase_service.ensure_session(request.session_id)
            session_state: Dict[str, Any] = session.get("state", {}) if session else {}

            # 3) Merge GPT metadata into session state (NEVER DOWNGRADE) — EXACTLY AS OLD LOGIC
            if metadata:
                for key, value in metadata.dict().items():
                    if value is not None:
                        session_state[key] = value
                    elif key in session_state:
                        setattr(metadata, key, session_state[key])

                # (compat) keep product_name and last_product aligned without changing the original rule
                if getattr(metadata, "product_name", None) and not session_state.get("last_product"):
                    session_state["last_product"] = metadata.product_name
                elif session_state.get("last_product") and not getattr(metadata, "product_name", None):
                    metadata.product_name = session_state["last_product"]

            # 4) Save updated state back to Supabase
            await supabase_service.update_session_state(request.session_id, session_state)

            # 5) Route by category (catalog preload if needed)
            enhanced_response = await self._route_by_category(
                category=category,
                request=request,
                base_response=gpt_response.natural_response,
                session_state=session_state,
            )

            # 🧹 5.1) Clean up GPT formatting labels before sending
            if enhanced_response:
                for marker in ["Summary:", "Clarification:", "Next step:", "1)", "2)", "3)"]:
                    enhanced_response = enhanced_response.replace(marker, "").strip()

            # 6) Handle PDF generation
            if ready_for_pdf:
                order_data = self._build_order_data(request.session_id, session_state)
                logger.info(f"[PDF DEBUG] ready_for_pdf=True, session_state={session_state}")
                logger.info(f"[PDF DEBUG] order_data={order_data}")

                if order_data:
                    # Step 1️⃣: Generate PDF and upload to Supabase (also inserts invoice row)
                    pdf_url = await pdf_service.generate_invoice(request.session_id, order_data)
                    logger.info(f"[PDF DEBUG] pdf_url={pdf_url}")

                    if pdf_url:
                        # Step 2️⃣: Send WhatsApp message with invoice link (use request.phone_number)
                        try:
                            if request.phone_number:
                                await whatsapp_service.send_message(
                                    request.phone_number,
                                    f"✅ Your order has been confirmed!\nHere’s your invoice:\n{pdf_url}"
                                )
                        except Exception as e:
                            logger.error(f"[WHATSAPP DEBUG] Error sending invoice link: {e}", exc_info=True)

                        # Also append link to the chat response
                        enhanced_response += f"\n\n📄 Your invoice has been generated: {pdf_url}"
                    else:
                        enhanced_response += "\n\n⚠️ Invoice generated locally but upload failed. Please contact support."
                else:
                    logger.warning("[PDF DEBUG] Order data incomplete — skipping PDF generation.")

            # 📝 Log bot response
            await supabase_service.save_message(
                session_id=request.session_id,
                role="assistant",
                message=enhanced_response,
                metadata=metadata.dict() if metadata else {}
            )

            return ChatResponse(
                session_id=request.session_id,
                response=enhanced_response,
                category=category,
                ready_for_pdf=ready_for_pdf,
                metadata=metadata.dict() if metadata else {},
            )

        except Exception as e:
            logger.error(f"Error in router processing: {str(e)}", exc_info=True)
            fallback_msg = (
                "I’m sorry — I’m having trouble responding right now. Could you please try again?"
            )

            # 📝 Log bot error response
            await supabase_service.save_message(
                session_id=request.session_id,
                role="assistant",
                message=fallback_msg,
                metadata={}
            )

            return ChatResponse(
                session_id=request.session_id,
                response=fallback_msg,
                category="Relationship & Psychology",
                ready_for_pdf=False,
                metadata={},
            )

    async def _route_by_category(
        self,
        category: str,
        request: ChatRequest,
        base_response: str,
        session_state: Dict[str, Any],
    ) -> str:
        """For Products & Sourcing, preload WooCommerce catalog if not already cached."""
        try:
            if category == "Products & Sourcing" and "catalog" not in session_state:
                products = woocommerce_service.list_products(per_page=100)
                session_state["catalog"] = [
                    {"name": p.name, "description": p.description or ""}
                    for p in products
                ]
                logger.info(
                    f"Cached {len(session_state['catalog'])} products for session {request.session_id}"
                )
            return base_response
        except Exception as e:
            logger.error(f"Error routing category {category}: {str(e)}", exc_info=True)
            return base_response

    def _build_order_data(self, session_id: str, state: Dict[str, Any]) -> Optional[OrderData]:
        """Builds an OrderData object from session state (only when complete)."""
        try:
            product = state.get("last_product") or state.get("product_name")
            required = [
                product,
                state.get("quantity"),
                state.get("quantity_unit"),
                state.get("destination_country"),
                state.get("city"),
                state.get("street_address"),
                state.get("shipping_incoterm"),
                state.get("payment_option"),
            ]
            if all(required):
                return OrderData(
                    session_id=session_id,
                    products=[
                        {
                            "name": product,
                            "price": 0.0,
                            "quantity": state["quantity"],
                            "quantity_unit": state["quantity_unit"],
                        }
                    ],
                    quantity=state["quantity"],
                    quantity_unit=state["quantity_unit"],
                    destination_country=state["destination_country"],
                    city=state["city"],
                    street_address=state["street_address"],
                    shipping_incoterm=state["shipping_incoterm"],
                    payment_option=state["payment_option"],
                )
            # Log what’s missing to speed up debugging
            missing = []
            labels = ["product", "quantity", "quantity_unit", "destination_country", "city",
                      "street_address", "shipping_incoterm", "payment_option"]
            values = [product, state.get("quantity"), state.get("quantity_unit"),
                      state.get("destination_country"), state.get("city"), state.get("street_address"),
                      state.get("shipping_incoterm"), state.get("payment_option")]
            for k, v in zip(labels, values):
                if not v:
                    missing.append(k)
            logger.warning(f"[PDF DEBUG] OrderData missing fields: {missing}")
            return None
        except Exception as e:
            logger.error(f"Error building order data: {e}", exc_info=True)
            return None


# Global instance
router = Router()
