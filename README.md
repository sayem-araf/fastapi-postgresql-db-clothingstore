# FastAPI PostgreSQL Demo (Clothing Store API)

A RESTful API service built with FastAPI and PostgreSQL for managing a clothing store with products, orders, customers, and categories.

## Features
- **Product Management**: Browse products with category, price, and stock information
- **Customer Management**: User registration and login
- **Order System**: Place orders with automatic stock management
- **Categories**: Organize products by categories
- **Statistics**: View customer spending and product revenue analytics
- **Database Migration**: Automatic schema setup and sample data seeding
- **REST Client Testing**: Test endpoints using VSCode REST Client extension

## Technology Stack
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Relational database (Neon cloud database)
- **psycopg** - PostgreSQL adapter for Python
- **Docker** - Containerization (optional)

## API Endpoints

### Public Endpoints (No authentication required)
- `GET /` - API info
- `GET /products` - List all products with details
- `GET /categories` - List all categories
- `GET /categories/{id}` - Get specific category
- `POST /users` - Create new user (registration)
- `POST /users/login` - User login

### Order Endpoints
- `POST /orders` - Place a new order (decreases stock automatically)
- `GET /orders` - List all orders (optional: filter by customer_id)

### Category Management
- `POST /categories` - Create new category

### Statistics Endpoints
- `GET /statistics/users` - Customer order statistics
- `GET /statistics/products` - Product revenue statistics

## Setup and Installation

### Running Locally (Without Docker)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   Make sure `.env` file exists with:
   ```
   DATABASE_URL=your_postgresql_connection_string
   API_URL=http://localhost:8080
   MODE=development
   ```

3. **Run the server:**
   ```bash
   fastapi dev app/main.py
   ```
   
   The API will be available at `http://localhost:8080`

### Running with Docker Compose

1. **Build and start containers:**
   ```bash
   docker-compose up --build
   ```

2. **Access the API:**
   - API: `http://localhost:8080`
   - Interactive docs: `http://localhost:8080/docs`

## Testing the API

### Method 1: REST Client Extension (Recommended)
1. Install the REST Client extension in VS Code (`humao.rest-client`)
2. Open `test/categories.http`
3. Click "Send Request" above any endpoint to test it

### Method 2: Swagger UI
Visit `http://localhost:8080/docs` for interactive API documentation where you can test all endpoints.

### Method 3: curl
```bash
# Get all products
curl http://localhost:8080/products

# Create a user
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'

# Place an order
curl -X POST http://localhost:8080/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_id": 1, "product_id": 1, "quantity": 2}'
```

## Database

### Schema
The database includes the following tables:
- **categories** - Product categories
- **products** - Products with price, stock, and category
- **customers** - User accounts
- **orders** - Customer orders
- **order_items** - Individual items in orders

### Automatic Migration
When the API starts, it automatically:
1. Creates all necessary tables (if they don't exist)
2. Adds/updates columns as needed
3. Seeds sample data (if database is empty)

### Making Schema Changes
Edit `db/schema.sql` and add new columns using:
```sql
ALTER TABLE table_name ADD COLUMN IF NOT EXISTS column_name TYPE;
```

Restart the server to apply changes.

## Project Structure
```
├── app/
│   ├── main.py           # FastAPI application and endpoints
│   └── db_migration.py   # Database setup and seeding
├── db/
│   ├── schema.sql        # Database schema definition
│   └── seed.sql          # Sample data for testing
├── test/
│   └── categories.http   # REST Client test requests
├── .env                  # Environment variables
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Sample Data
The API comes pre-loaded with:
- 4 categories (T-Shirts, Jeans, Shoes, Accessories)
- 14 products across categories
- 6 sample customers
- 54 sample orders with order items

## Development Notes
- The API uses row_factory=dict_row to return results as dictionaries
- Stock automatically decreases when orders are placed
- Email addresses must be unique for user registration
- All endpoints return JSON responses

## Cloud Deployment
- Set `DATABASE_URL` environment variable to your production PostgreSQL connection string
- Set `MODE=production` in environment variables
- Docker-compose is only for local development

## API Version
Current version: v0.3
