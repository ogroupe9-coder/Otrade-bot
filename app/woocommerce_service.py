"""
WooCommerce service for OTRADE Bot product integration
"""
import requests
from requests.auth import HTTPBasicAuth
from typing import List, Optional
import logging
import re

from .config import config
from .schemas import ProductInfo

logger = logging.getLogger(__name__)


class WooCommerceService:
    def __init__(self):
        self.base_url = getattr(config, "woocommerce_url", "")
        self.consumer_key = getattr(config, "woocommerce_consumer_key", "")
        self.consumer_secret = getattr(config, "woocommerce_consumer_secret", "")
        self.auth = HTTPBasicAuth(self.consumer_key, self.consumer_secret)

    def _is_configured(self) -> bool:
        return all([self.base_url, self.consumer_key, self.consumer_secret])

    def get_product_by_name(self, name: str) -> Optional[ProductInfo]:
        try:
            if not self._is_configured():
                return None
            url = f"{self.base_url}/wp-json/wc/v3/products"
            params = {"search": name, "per_page": 1, "status": "publish"}
            resp = requests.get(url, auth=self.auth, params=params, timeout=12)
            resp.raise_for_status()
            products = resp.json()
            if products:
                return self._to_product(products[0])
            return None
        except Exception as e:
            logger.error(f"Error searching product by name '{name}': {str(e)}")
            return None

    def list_products(self, per_page: int = 20, page: int = 1) -> List[ProductInfo]:
        try:
            if not self._is_configured():
                return []
            url = f"{self.base_url}/wp-json/wc/v3/products"
            params = {"per_page": per_page, "page": page, "status": "publish"}
            resp = requests.get(url, auth=self.auth, params=params, timeout=12)
            resp.raise_for_status()
            return [self._to_product(p) for p in (resp.json() or [])]
        except Exception as e:
            logger.error(f"Error listing products: {str(e)}")
            return []

    def check_stock(self, product_id: int) -> Optional[int]:
        try:
            if not self._is_configured():
                return None
            url = f"{self.base_url}/wp-json/wc/v3/products/{product_id}"
            resp = requests.get(url, auth=self.auth, timeout=12)
            resp.raise_for_status()
            return resp.json().get("stock_quantity")
        except Exception as e:
            logger.error(f"Error checking stock for product {product_id}: {str(e)}")
            return None

    def search_products(self, query: str, per_page: int = 10) -> List[ProductInfo]:
        try:
            if not self._is_configured():
                return []
            url = f"{self.base_url}/wp-json/wc/v3/products"
            params = {"search": query, "per_page": per_page, "status": "publish"}
            resp = requests.get(url, auth=self.auth, params=params, timeout=12)
            resp.raise_for_status()
            return [self._to_product(p) for p in (resp.json() or [])]
        except Exception as e:
            logger.error(f"Error searching products with query '{query}': {str(e)}")
            return []

    def format_products_for_gpt(self, products: List[ProductInfo]) -> str:
        if not products:
            return "I couldn’t find any matching products. Please try other keywords."
        lines = ["Here are some available products:"]
        for i, p in enumerate(products[:5], 1):
            stock = f" (Stock: {p.stock_quantity})" if p.stock_quantity is not None else ""
            price_display = "Price on request" if not p.price or p.price == 0.0 else f"${p.price:.2f}"
            desc = self._strip_html(p.description)[:120]
            lines.append(f"{i}. {p.name}: {price_display}{stock}")
            if desc:
                lines.append(f"   {desc}...")
        return "\n".join(lines)

    def normalize_product_name(self, name: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()

    def _strip_html(self, text: str) -> str:
        return re.sub(r"<[^>]+>", " ", text or "").strip()

    def _to_product(self, p: dict) -> ProductInfo:
        return ProductInfo(
            id=p["id"],
            name=p.get("name", "Unknown"),
            price=float(p.get("price") or 0.0),
            stock_quantity=p.get("stock_quantity"),
            description=p.get("short_description", "") or p.get("description", ""),
        )


# Global instance
woocommerce_service = WooCommerceService()
