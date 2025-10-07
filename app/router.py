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

logger = logging.getLogger(__name__)


class Router:
    async def process_request(self, request: ChatRequest) -> ChatResponse:
        try:
            # 📝 Log user message
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

            # 2) Load current session state
            session = await supabase_service.ensure_session(request.session_id)
            session_state: Dict[str, Any] = session.get("state", {}) if session else {}

            # 3) Merge GPT metadata into session state (never downgrade existing values)
            if metadata:
                if metadata.product_name:
                    session_state["last_product"] = metadata.product_name
                elif "last_product" in session_state:
                    metadata.product_name = session_state["last_product"]

                if metadata.quantity is not None:
                    session_state["quantity"] = metadata.quantity
                elif "quantity" in session_state:
                    metadata.quantity = session_state["quantity"]

                if metadata.destination_country:
                    session_state["destination_country"] = metadata.destination_country
                elif "destination_country" in session_state:
                    metadata.destination_country = session_state["destination_country"]

                if metadata.city:
                    session_state["city"] = metadata.city
                elif "city" in session_state:
                    metadata.city = session_state["city"]

                if metadata.street_address:
                    session_state["street_address"] = metadata.street_address
                elif "street_address" in session_state:
                    metadata.street_address = session_state["street_address"]

                if metadata.shipping_incoterm:
                    session_state["shipping_incoterm"] = metadata.shipping_incoterm
                elif "shipping_incoterm" in session_state:
                    metadata.shipping_incoterm = session_state["shipping_incoterm"]

                if metadata.payment_option:
                    session_state["payment_option"] = metadata.payment_option
                elif "payment_option" in session_state:
                    metadata.payment_option = session_state["payment_option"]

            # 4) Save updated state back to Supabase
            await supabase_service.update_session_state(request.session_id, session_state)

            # 5) Route by category (catalog preload if needed)
            enhanced_response = await self._route_by_category(
                category=category,
                request=request,
                base_response=gpt_response.natural_response,
                session_state=session_state,
            )

            # 6) Handle PDF generation
            if ready_for_pdf:
                order_data = self._build_order_data(request.session_id, session_state)
                if order_data:
                    pdf_url = await pdf_service.generate_invoice(request.session_id, order_data)
                    if pdf_url:
                        enhanced_response += f"\n\n📄 Your invoice has been generated: {pdf_url}"
                    else:
                        enhanced_response += "\n\n⚠️ Invoice generated locally but upload failed. Please contact support."

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
            fallback_msg = "I’m sorry — I’m having trouble responding right now. Could you please try again?"

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
                logger.info(f"Cached {len(session_state['catalog'])} products for session {request.session_id}")
            return base_response
        except Exception as e:
            logger.error(f"Error routing category {category}: {str(e)}", exc_info=True)
            return base_response

    def _build_order_data(self, session_id: str, state: Dict[str, Any]) -> Optional[OrderData]:
        """Builds an OrderData object from session state (only when complete)."""
        try:
            required = [
                state.get("last_product"),
                state.get("quantity"),
                state.get("destination_country"),
                state.get("city"),
                state.get("street_address"),
                state.get("shipping_incoterm"),
                state.get("payment_option"),
            ]
            if all(required):
                return OrderData(
                    session_id=session_id,
                    products=[{
                        "name": state["last_product"],
                        "price": 0.0,
                        "quantity": state["quantity"]
                    }],
                    quantity=state["quantity"],
                    destination_country=state["destination_country"],
                    city=state["city"],
                    street_address=state["street_address"],
                    shipping_incoterm=state["shipping_incoterm"],
                    payment_option=state["payment_option"],
                )
            return None
        except Exception as e:
            logger.error(f"Error building order data: {e}", exc_info=True)
            return None


# Global instance
router = Router()
