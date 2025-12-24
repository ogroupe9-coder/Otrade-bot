# OTRADE Bot - API Analysis & Testing Guide

## 📋 Bot Overview

**OTRADE Bot** is an AI-powered wholesale trading assistant built with FastAPI. It integrates with:
- **OpenAI GPT** for natural language processing
- **Twilio WhatsApp** for messaging
- **WooCommerce** for product catalog
- **Supabase** for database and storage
- **ReportLab** for PDF invoice generation

## 🏗️ Architecture

### Main Components

1. **main.py** - FastAPI application with 3 main endpoints
2. **router.py** - Request routing and state management
3. **gpt_service.py** - OpenAI integration
4. **whatsapp_service.py** - Twilio WhatsApp integration
5. **woocommerce_service.py** - Product catalog integration
6. **supabase_service.py** - Database and storage operations
7. **pdf_service.py** - Invoice generation

### Database Schema (Supabase)

The bot uses the following tables:
- **sessions** - Conversation sessions with state tracking
- **conversations** - Message history (user + assistant)
- **invoices** - Generated invoices with PDF URLs

## 🔌 API Endpoints

### 1. Root Endpoint
```
GET /
```
Returns API status and version information.

**Response:**
```json
{
  "message": "OTRADE Bot API is running",
  "version": "1.0.0"
}
```

---

### 2. Health Check
```
GET /health
```
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "ok"
}
```

---

### 3. Chat Endpoint
```
POST /chat
```
Main chat interface for testing the bot.

**Request Body:**
```json
{
  "session_id": "test_session_001",
  "message": "I want to order rice",
  "phone_number": "+1234567890"  // optional
}
```

**Response:**
```json
{
  "session_id": "test_session_001",
  "response": "I'd be happy to help you order rice! To provide you with an accurate quote...",
  "category": "Products & Sourcing",
  "ready_for_pdf": false,
  "metadata": {
    "category": "Products & Sourcing",
    "ready_for_pdf": false,
    "product_name": "rice",
    "quantity": null,
    "quantity_unit": null,
    "destination_country": null,
    "city": null,
    "street_address": null,
    "shipping_incoterm": null,
    "payment_option": null
  }
}
```

---

### 4. WhatsApp Webhook
```
POST /webhook/whatsapp
```
Receives incoming WhatsApp messages from Twilio.

**Request (Form Data):**
```
From: whatsapp:+1234567890
To: whatsapp:+0987654321
Body: I need to order cotton
MessageSid: SM1234567890abcdef
```

**Response:**
```
200 OK (empty body)
```

## 🔄 Conversation Flow

The bot follows this order collection flow:

1. **Product Inquiry** - User mentions product name
   - Category: `Products & Sourcing`
   - Bot asks for quantity

2. **Quantity Specification** - User provides quantity and unit
   - Tracked: `quantity`, `quantity_unit` (carton/pallet/container)

3. **Shipping Details** - User provides location
   - Tracked: `destination_country`, `city`, `street_address`

4. **Shipping Terms** - User chooses shipping method
   - Tracked: `shipping_incoterm` (FOB/CIF)

5. **Payment Terms** - User selects payment option
   - Tracked: `payment_option`

6. **Order Confirmation** - When all fields are complete
   - `ready_for_pdf: true`
   - Bot generates PDF invoice
   - Invoice uploaded to Supabase Storage
   - WhatsApp message sent with invoice link

## 📦 Required Order Fields

For PDF generation, these fields must be collected:

| Field | Description | Example |
|-------|-------------|---------|
| `product_name` | Product being ordered | "Rice" |
| `quantity` | Order quantity | 50 |
| `quantity_unit` | Unit type | "carton" |
| `destination_country` | Shipping country | "Pakistan" |
| `city` | Shipping city | "Karachi" |
| `street_address` | Delivery address | "123 Main Street" |
| `shipping_incoterm` | Shipping terms | "FOB" or "CIF" |
| `payment_option` | Payment method | "30-day credit" |

## 🧪 Testing with Postman

### Setup

1. Import `OTRADE_Bot_Postman_Collection.json` into Postman
2. Ensure the bot is running locally: `python run_bot.py`
3. The collection uses base URL: `http://localhost:8000`

### Test Scenarios

#### Scenario 1: Complete Order Flow
Run these requests in sequence with the same `session_id`:

1. **Product Inquiry** - "I want to order rice"
2. **Specify Quantity** - "I need 50 cartons"
3. **Provide Shipping Details** - "Ship to Karachi, Pakistan. Address is 123 Main Street. I prefer FOB shipping and 30-day credit payment"
4. **Confirm Order** - "Yes, please confirm the order"

**Expected Result:** Final response should include a PDF invoice URL.

#### Scenario 2: General Question
Send a non-product related message:
- "How can I improve my business relationships?"

**Expected Result:** 
- Category: `Relationship & Psychology`
- `ready_for_pdf: false`

#### Scenario 3: WhatsApp Simulation
Use the WhatsApp webhook endpoint to simulate Twilio messages.

**Expected Result:** Bot processes message and attempts to send reply via WhatsApp.

## 🔑 Environment Variables

The bot requires these environment variables (in `.env`):

```env
# OpenAI
OPENAI_API_KEY=sk-...

# Twilio WhatsApp
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_NUMBER=whatsapp:+...

# Supabase
SUPABASE_URL=https://...supabase.co
SUPABASE_KEY=eyJ...

# WooCommerce (optional)
WOOCOMMERCE_URL=https://...
WOOCOMMERCE_KEY=ck_...
WOOCOMMERCE_SECRET=cs_...
```

## 📝 Response Categories

The GPT service categorizes messages into:

1. **Products & Sourcing** - Product orders, pricing, catalog
2. **Relationship & Psychology** - General questions (default)

## 🎯 Key Features

✅ Conversational AI with context tracking  
✅ Multi-turn order collection  
✅ Automatic PDF invoice generation  
✅ WhatsApp integration via Twilio  
✅ WooCommerce product catalog integration  
✅ Persistent session state in Supabase  
✅ Message history logging  

## 🚀 Running the Bot

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
# Create .env file with required credentials

# Run the bot
python run_bot.py

# API will be available at http://localhost:8000
```

## 📊 Monitoring

- Check `/health` for uptime monitoring
- Review Supabase `conversations` table for message logs
- Check `invoices` table for order history
- Monitor `sessions` table for active conversations

## 🐛 Troubleshooting

**Issue:** "ready_for_pdf is true but no PDF generated"
- **Cause:** Missing required order fields
- **Solution:** Check logs for missing fields, ensure all 8 required fields are collected

**Issue:** WhatsApp messages not sending
- **Cause:** Invalid Twilio credentials or phone number format
- **Solution:** Verify `.env` credentials and phone number format (include country code)

**Issue:** Product catalog not loading
- **Cause:** WooCommerce credentials missing or incorrect
- **Solution:** Verify WooCommerce URL and API keys in `.env`

---

**Created:** 2025-12-17  
**Bot Version:** 1.0.0  
**API Framework:** FastAPI 0.95+
