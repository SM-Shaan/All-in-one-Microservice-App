con# Product Service

Product catalog management microservice using MongoDB.

## Overview

The Product Service manages the e-commerce product catalog including:
- Product information (name, description, price)
- Categories and tags
- Stock management
- Product images
- Search and filtering

## Technology Stack

- **Framework**: FastAPI
- **Database**: MongoDB (NoSQL)
- **Language**: Python 3.11+
- **Driver**: Motor (async MongoDB driver)

## Why MongoDB for Products?

Products are a great fit for MongoDB because:

1. **Flexible Schema**: Products can have different attributes
   - Electronics have specifications
   - Clothing has sizes and colors
   - Books have authors and ISBNs
   - No need to add columns for every product type!

2. **Nested Documents**: Store related data together
   ```json
   {
     "name": "Laptop",
     "specifications": {
       "brand": "TechCorp",
       "ram": "16GB",
       "storage": "512GB SSD"
     }
   }
   ```

3. **Arrays**: Multiple values in one field
   ```json
   {
     "tags": ["laptop", "gaming", "electronics"],
     "images": ["img1.jpg", "img2.jpg", "img3.jpg"]
   }
   ```

4. **Easy Scaling**: MongoDB scales horizontally

## Architecture

```
Product Service (Port 8002)
     ↓
Product Repository
     ↓
Motor (Async Driver)
     ↓
MongoDB
```

## API Endpoints

### Products

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/products` | Create new product |
| GET | `/api/v1/products` | List products (with filters) |
| GET | `/api/v1/products/{id}` | Get product by ID |
| PUT | `/api/v1/products/{id}` | Update product |
| DELETE | `/api/v1/products/{id}` | Delete product |
| PATCH | `/api/v1/products/{id}/stock` | Update stock |
| GET | `/api/v1/products/sku/{sku}` | Get by SKU |
| GET | `/api/v1/products/featured` | Get featured products |
| GET | `/api/v1/products/category/{category}` | Get by category |
| GET | `/api/v1/products/search/tags` | Search by tags |

### Advanced Filtering

The list endpoint supports powerful filtering:

```bash
# Search for laptops
GET /api/v1/products?search=laptop

# Filter by category and price range
GET /api/v1/products?category=Electronics&min_price=500&max_price=2000

# Only in-stock products
GET /api/v1/products?in_stock_only=true

# Sort by price (ascending)
GET /api/v1/products?sort_by=price&sort_order=asc

# Combine filters
GET /api/v1/products?category=Electronics&search=gaming&min_price=1000&in_stock_only=true
```

## Running the Service

### Prerequisites

- Python 3.11+
- MongoDB running (via Docker)

### Step 1: Start MongoDB

```bash
# From project root
cd E:\microservices-platform
docker-compose up -d mongodb
```

### Step 2: Install Dependencies

```bash
cd services/product-service
pip install -r requirements.txt
```

### Step 3: Run the Service

```bash
python run.py
```

Or:
```bash
uvicorn app.main:app --reload --port 8002
```

### Step 4: Access the API

- API: http://localhost:8002
- Swagger Docs: http://localhost:8002/docs
- ReDoc: http://localhost:8002/redoc

## Testing the API

### Create a Product

```bash
curl -X POST http://localhost:8002/api/v1/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Gaming Laptop Pro",
    "description": "High-performance gaming laptop with RTX 4080 GPU",
    "sku": "LAPTOP-001",
    "price": 1299.99,
    "original_price": 1499.99,
    "category": "Electronics",
    "subcategory": "Computers",
    "tags": ["laptop", "gaming", "rtx", "high-performance"],
    "stock": 50,
    "images": [
      "https://example.com/laptop1.jpg",
      "https://example.com/laptop2.jpg"
    ],
    "specifications": {
      "brand": "TechCorp",
      "model": "GX-2000",
      "ram": "32GB DDR5",
      "storage": "1TB NVMe SSD",
      "gpu": "RTX 4080",
      "screen": "15.6 inch 240Hz"
    }
  }'
```

### List Products

```bash
# Get all products
curl http://localhost:8002/api/v1/products

# Search for laptops
curl "http://localhost:8002/api/v1/products?search=laptop"

# Filter by category
curl "http://localhost:8002/api/v1/products?category=Electronics"

# Price range
curl "http://localhost:8002/api/v1/products?min_price=1000&max_price=2000"
```

### Get Product by ID

```bash
curl http://localhost:8002/api/v1/products/{product_id}
```

### Update Product

```bash
curl -X PUT http://localhost:8002/api/v1/products/{product_id} \
  -H "Content-Type: application/json" \
  -d '{
    "price": 1199.99,
    "stock": 45
  }'
```

### Update Stock

```bash
# Add 10 items to stock
curl -X PATCH "http://localhost:8002/api/v1/products/{product_id}/stock?quantity_change=10"

# Remove 5 items from stock
curl -X PATCH "http://localhost:8002/api/v1/products/{product_id}/stock?quantity_change=-5"
```

## MongoDB vs PostgreSQL

| Feature | MongoDB (Product Service) | PostgreSQL (User Service) |
|---------|---------------------------|---------------------------|
| Type | NoSQL (Document) | SQL (Relational) |
| Schema | Flexible | Fixed |
| Storage | JSON-like documents | Tables with rows |
| Relationships | Embedded or referenced | Foreign keys |
| Queries | JavaScript-like | SQL |
| Best For | Flexible data, nested objects | Structured data, complex joins |

### Example Comparison

**MongoDB Document:**
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "name": "Laptop",
  "specs": {
    "ram": "16GB",
    "cpu": "Intel i7"
  },
  "tags": ["laptop", "gaming"]
}
```

**PostgreSQL Tables:**
```sql
-- products table
CREATE TABLE products (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    created_at TIMESTAMP
);

-- product_specs table
CREATE TABLE product_specs (
    id UUID PRIMARY KEY,
    product_id UUID REFERENCES products(id),
    key VARCHAR(100),
    value VARCHAR(255)
);

-- product_tags table
CREATE TABLE product_tags (
    product_id UUID REFERENCES products(id),
    tag VARCHAR(100)
);
```

## MongoDB Queries Explained

### Find All Products
```python
await collection.find().to_list(100)
```

### Find by Category
```python
await collection.find({"category": "Electronics"}).to_list(100)
```

### Find with Price Range
```python
await collection.find({
    "price": {"$gte": 100, "$lte": 500}
}).to_list(100)
```

### Search in Name/Description
```python
await collection.find({
    "$or": [
        {"name": {"$regex": "laptop", "$options": "i"}},
        {"description": {"$regex": "laptop", "$options": "i"}}
    ]
}).to_list(100)
```

### Complex Query
```python
await collection.find({
    "category": "Electronics",
    "price": {"$gte": 1000},
    "stock": {"$gt": 0},
    "tags": {"$in": ["laptop", "gaming"]}
}).sort("price", -1).to_list(100)
```

## Project Structure

```
product-service/
├── app/
│   ├── main.py                  # FastAPI application
│   ├── core/
│   │   └── config.py           # Configuration
│   ├── db/
│   │   ├── mongodb.py          # MongoDB connection
│   │   └── repositories/
│   │       └── product_repository.py  # Data access
│   ├── models/
│   │   └── product.py          # Pydantic models
│   └── api/
│       └── routes/
│           ├── health.py       # Health checks
│           └── products.py     # Product endpoints
├── Dockerfile
├── requirements.txt
├── run.py
└── README.md
```

## What You've Learned

### 1. NoSQL Databases
- Document-based storage
- Flexible schema
- Nested documents
- Arrays in documents

### 2. MongoDB Operations
- insert_one(), find(), update_one(), delete_one()
- Query operators: $gte, $lte, $in, $regex, $or
- Sorting and pagination
- Aggregation (future)

### 3. Motor (Async Driver)
- Async MongoDB operations
- Connection pooling
- Non-blocking queries

### 4. Microservice Architecture
- Multiple services with different databases
- Service isolation
- Different ports for different services

## Common MongoDB Operations

### Connect to MongoDB CLI

```bash
# Access MongoDB shell
docker exec -it microservices-mongodb mongosh -u admin -p admin123

# Switch to products database
use products

# List collections
show collections

# Find all products
db.products.find().pretty()

# Find products in Electronics category
db.products.find({category: "Electronics"}).pretty()

# Count products
db.products.countDocuments()

# Exit
exit
```

## Next Steps

Once comfortable with Phase 4:

1. **Test all endpoints** using Swagger UI
2. **Compare** MongoDB queries with PostgreSQL queries
3. **Add more products** with different categories
4. **Test advanced filters** (price range, search, etc.)
5. **Move to Phase 5** - Service-to-service communication

## Resources

- [MongoDB Documentation](https://docs.mongodb.com/)
- [Motor Documentation](https://motor.readthedocs.io/)
- [MongoDB Query Operators](https://docs.mongodb.com/manual/reference/operator/query/)
- [NoSQL vs SQL](https://www.mongodb.com/nosql-explained/nosql-vs-sql)
