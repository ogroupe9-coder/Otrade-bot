"""
Pydantic schemas for OTRADE Bot
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
from datetime import datetime


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    message: str
    created_at: Optional[datetime] = None


class ChatRequest(BaseModel):
    session_id: str
    message: str
    phone_number: Optional[str] = None


class GPTMetadata(BaseModel):
    category: str = "Relationship & Psychology"
    ready_for_pdf: bool = False
    product_name: Optional[str] = None
    quantity: Optional[int] = None
    quantity_unit: Optional[str] = None  # carton, pallet, container, etc.
    destination_country: Optional[str] = None
    city: Optional[str] = None
    street_address: Optional[str] = None
    shipping_incoterm: Optional[str] = None  # FOB / CIF
    payment_option: Optional[str] = None

    def items(self):
        """Compatibility: behave like a dict for easy iteration"""
        return {
            "category": self.category,
            "ready_for_pdf": self.ready_for_pdf,
            "product_name": self.product_name,
            "quantity": self.quantity,
            "destination_country": self.destination_country,
            "city": self.city,
            "street_address": self.street_address,
            "shipping_incoterm": self.shipping_incoterm,
            "payment_option": self.payment_option,
        }.items()


class ChatResponse(BaseModel):
    session_id: str
    response: str
    category: str
    ready_for_pdf: bool = False
    metadata: Union[GPTMetadata, Dict[str, Any], None] = None


class GPTResponse(BaseModel):
    natural_response: str
    metadata: GPTMetadata


class ProductInfo(BaseModel):
    id: int
    name: str
    price: float
    stock_quantity: Optional[int] = None
    description: Optional[str] = None


class OrderData(BaseModel):
    session_id: str
    products: List[Dict[str, Any]]
    quantity: int
    quantity_unit: str
    destination_country: str
    city: str
    street_address: str
    shipping_incoterm: str  # FOB or CIF
    payment_option: str


class InvoiceRecord(BaseModel):
    id: Optional[str] = None
    session_id: str
    invoice_number: str
    pdf_url: Optional[str] = None
    order_data: Dict[str, Any]
    total_amount: Optional[float] = None
    currency: str = "USD"
    status: str = "pending"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ConversationRecord(BaseModel):
    id: Optional[str] = None
    session_id: str
    role: str
    message: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


class WhatsAppMessage(BaseModel):
    From: str
    To: str
    Body: str
    MessageSid: str
