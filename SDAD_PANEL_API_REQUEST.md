# SDAD Panel API - Stock Management Integration

## Overview

This document outlines the API requirements for integrating the **SDAD Panel (Warehouse Management System)** with the **WHDASH Enterprise Hub**. The integration enables real-time synchronization of stock data, warehouse information, and product catalog.

---

## Base Configuration

| Item | Value |
|------|-------|
| **Panel Base URL** | `https://panel.sdadparts.com` |
| **Authentication** | Bearer Token (JWT) |
| **Response Format** | JSON |

---

## Required API Endpoints

### 1. Authentication

**POST** `/api/auth/login`

Authenticate and receive access token.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200):**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin"
  }
}
```

---

### 2. Stock Management - Products

**GET** `/api/stock-management/products`

Retrieve all products with stock information.

**Headers:**
```
Authorization: Bearer {token}
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `role` | string | No | Set to `admin` for full data |
| `warehouse` | string | No | Filter by warehouse name |
| `category` | string | No | Filter by category name |
| `page` | integer | No | Page number (default: 1) |
| `per_page` | integer | No | Items per page (default: 100) |

**Response (200):**
```json
{
  "success": true,
  "products": [
    {
      "product_code": "BRK-001",
      "name": "Brake Pad Set - Front",
      "sku": "BRK-PAD-FRT",
      "category": "Brakes",
      "brand": "Brembo",
      "warehouse": "Peyvast",
      "stock_location": "A-01-01",
      "quantity": 150,
      "initial_stock": 200,
      "min_stock": 20,
      "max_stock": 500,
      "unit": "pcs",
      "updated_at": "2026-04-02T12:00:00Z"
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 2,
    "total_items": 155,
    "per_page": 100
  }
}
```

---

### 3. Stock Management - Single Product

**GET** `/api/stock-management/products/{product_code}`

Retrieve detailed information for a single product.

**Response (200):**
```json
{
  "success": true,
  "product": {
    "product_code": "BRK-001",
    "name": "Brake Pad Set - Front",
    "sku": "BRK-PAD-FRT",
    "category": "Brakes",
    "brand": "Brembo",
    "warehouse": "Peyvast",
    "stock_location": "A-01-01",
    "quantity": 150,
    "initial_stock": 200,
    "min_stock": 20,
    "max_stock": 500,
    "unit": "pcs",
    "updated_at": "2026-04-02T12:00:00Z"
  }
}
```

---

### 4. Warehouses

**GET** `/api/warehouses`

Retrieve all warehouses.

**Response (200):**
```json
{
  "success": true,
  "warehouses": [
    {
      "id": 1,
      "name": "Peyvast",
      "code": "PYV-001",
      "location": "Main Warehouse",
      "is_active": true,
      "products_count": 155
    }
  ]
}
```

---

### 5. Categories

**GET** `/api/categories`

Retrieve all product categories.

**Response (200):**
```json
{
  "success": true,
  "categories": [
    {
      "id": 1,
      "name": "Brakes",
      "parent_id": null,
      "products_count": 12
    },
    {
      "id": 2,
      "name": "Filters",
      "parent_id": null,
      "products_count": 8
    }
  ]
}
```

---

### 6. Stock Summary

**GET** `/api/stock-management/summary`

Retrieve stock summary statistics.

**Response (200):**
```json
{
  "success": true,
  "summary": {
    "total_products": 155,
    "total_warehouse_quantity": 19250,
    "low_stock_count": 7,
    "out_of_stock_count": 3,
    "categories_count": 9,
    "warehouses_count": 1
  }
}
```

---

### 7. Low Stock Alerts

**GET** `/api/stock-management/low-stock`

Retrieve products below minimum stock level.

**Response (200):**
```json
{
  "success": true,
  "items": [
    {
      "product_code": "ELT-001",
      "name": "Alternator - 90A",
      "sku": "ELT-ALT-90A",
      "category": "Electrical",
      "warehouse": "Peyvast",
      "quantity": 15,
      "min_stock": 20,
      "max_stock": 50,
      "shortage": 5
    }
  ]
}
```

---

### 8. Out of Stock Items

**GET** `/api/stock-management/out-of-stock`

Retrieve products with zero quantity.

**Response (200):**
```json
{
  "success": true,
  "items": [
    {
      "product_code": "SUS-003",
      "name": "Strut Assembly - Rear",
      "sku": "SUS-STR-REP",
      "category": "Suspension",
      "warehouse": "Peyvast",
      "quantity": 0,
      "min_stock": 10,
      "max_stock": 40
    }
  ]
}
```

---

## Data Field Mapping

| SDAD Panel Field | WHDASH Field | Data Type | Description |
|-------------------|---------------|-----------|-------------|
| `product_code` | `product_code` | string | Unique product identifier |
| `name` | `name` | string | Product name |
| `sku` | `sku` | string | Stock Keeping Unit code |
| `category` | `category` | string | Product category name |
| `brand` | `brand` | string | Manufacturer/brand name |
| `warehouse` | `warehouse_name` | string | Warehouse location name |
| `stock_location` | `stock_location` | string | Bin/Location code (e.g., A-01-01) |
| `quantity` | `quantity` | integer | Current stock quantity |
| `initial_stock` | `initial_stock` | integer | Starting stock level |
| `min_stock` | `min_stock` | integer | Minimum stock threshold |
| `max_stock` | `max_stock` | integer | Maximum stock threshold |
| `unit` | `unit` | string | Unit of measure (default: pcs) |
| `updated_at` | `last_synced_at` | datetime | Last update timestamp |

---

## Error Responses

All endpoints return standard error responses:

**401 Unauthorized:**
```json
{
  "success": false,
  "error": "Invalid or expired token"
}
```

**404 Not Found:**
```json
{
  "success": false,
  "error": "Product not found"
}
```

**500 Internal Server Error:**
```json
{
  "success": false,
  "error": "Internal server error"
}
```

---

## Integration Notes

1. **Sync Frequency:** Recommended sync interval is every 5-15 minutes for real-time updates
2. **Authentication:** Token should be refreshed every 24 hours
3. **Pagination:** Use pagination for large datasets (>100 items)
4. **Filtering:** Utilize warehouse/category filters to reduce payload size
5. **Timestamps:** All timestamps should be in UTC (ISO 8601 format)

---

## Webhook Support (Optional)

For real-time updates, consider implementing webhooks:

**POST** `/api/webhooks/stock-update`

WHDASH can receive real-time notifications when stock levels change.

```json
{
  "event": "stock_updated",
  "product_code": "BRK-001",
  "previous_quantity": 150,
  "new_quantity": 145,
  "warehouse": "Peyvast",
  "timestamp": "2026-04-02T14:30:00Z"
}
```

---

## Contact

For API support or questions:
- **Technical Lead:** IT Department
- **Integration Support:** WHDASH Team
