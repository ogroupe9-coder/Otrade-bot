"""
PDF generation service for OTRADE Bot invoices
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
import logging

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .config import config
from .schemas import OrderData, InvoiceRecord
from .supabase_service import supabase_service

logger = logging.getLogger(__name__)


class PDFService:
    def __init__(self):
        # Use absolute path for local storage
        base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.output_dir = base_dir / getattr(config, "pdf_storage_path", "invoices")
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"PDF Service initialized - Storage path: {self.output_dir}")

    async def generate_invoice(self, session_id: str, order_data: OrderData) -> Optional[str]:
        """
        Generate invoice as a PDF file, save locally, upload to Supabase, and persist in DB.
        Returns a public clickable URL if upload succeeds, otherwise a local file path.
        """
        try:
            invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"invoice_{invoice_number}_{timestamp}.pdf"
            file_path = self.output_dir / filename

            # Generate PDF
            self._generate_pdf_invoice(order_data, invoice_number, file_path)

            # Compute total
            total_amount = sum(
                float(p.get("price", 0) or 0) * int(p.get("quantity", 1) or 1)
                for p in order_data.products
            )

            # Upload to Supabase
            pdf_url = await supabase_service.upload_pdf(str(file_path), filename)
            if not pdf_url:
                logger.warning(f"Invoice {invoice_number} generated but not uploaded, using local path.")
                pdf_url = str(file_path)

            # Save DB record
            invoice_record = InvoiceRecord(
                session_id=session_id,
                invoice_number=invoice_number,
                pdf_url=pdf_url,
                order_data=order_data.dict(),
                total_amount=total_amount,
                currency="USD",
                status="pending",
            )
            saved = await supabase_service.save_invoice(invoice_record)
            if not saved:
                logger.warning(f"Invoice {invoice_number} uploaded but DB insert failed.")

            logger.info(f"✅ Invoice {invoice_number} created → {pdf_url}")
            return pdf_url

        except Exception as e:
            logger.error(f"Error generating invoice: {str(e)}", exc_info=True)
            return None

    def _generate_pdf_invoice(self, order_data: OrderData, invoice_number: str, file_path: Path):
        """Generate PDF invoice with reportlab."""
        c = canvas.Canvas(str(file_path), pagesize=A4)
        width, height = A4

        y = height - 50
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "OTRADE INVOICE")
        y -= 30
        c.setFont("Helvetica", 10)
        c.drawString(50, y, f"Invoice Number: {invoice_number}")
        y -= 20
        c.drawString(50, y, f"Session ID: {order_data.session_id}")
        y -= 20
        c.drawString(50, y, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Shipping
        y -= 40
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "SHIPPING DETAILS")
        c.setFont("Helvetica", 10)
        y -= 20
        c.drawString(50, y, f"Destination Country: {order_data.destination_country}")
        y -= 20
        c.drawString(50, y, f"City: {order_data.city}")
        y -= 20
        c.drawString(50, y, f"Address: {order_data.street_address}")
        y -= 20
        c.drawString(50, y, f"Incoterm: {order_data.shipping_incoterm}")

        # Products
        y -= 40
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "PRODUCTS")
        c.setFont("Helvetica", 10)
        total = 0.0
        for p in order_data.products:
            y -= 20
            name = p.get("name", "Unknown Product")
            price = float(p.get("price", 0) or 0)
            qty = int(p.get("quantity", 1) or 1)
            subtotal = price * qty
            total += subtotal
            c.drawString(50, y, f"{name}: ${price:.2f} x {qty} = ${subtotal:.2f}")

        # Totals
        y -= 40
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "TOTAL")
        c.setFont("Helvetica", 10)
        y -= 20
        c.drawString(50, y, f"${total:.2f} USD")

        # Payment
        y -= 40
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "PAYMENT")
        y -= 20
        c.setFont("Helvetica", 10)
        c.drawString(50, y, f"Payment Option: {order_data.payment_option}")

        c.showPage()
        c.save()


# Global instance
pdf_service = PDFService()
