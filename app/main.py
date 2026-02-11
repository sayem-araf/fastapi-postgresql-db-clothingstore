from fastapi import FastAPI, HTTPException
import os, psycopg
from psycopg.rows import dict_row
from app.db_migration import migrate_schema, seed_sample_data

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg.connect(DATABASE_URL, autocommit=True, row_factory=dict_row)

app = FastAPI()

# Run DB migration 
try:
    migrate_schema()
    seed_sample_data()
except Exception as e:
    print("ERROR: DB Migration failed:", str(e))

@app.get("/")
def get_root():
    return {"msg": "Clothing Store v0.3"}

# ----------------------
# User endpoints (Basic - no auth for now)
# ----------------------
@app.post("/users")
def create_user(data: dict):
    name = data.get("name")
    email = data.get("email")
    if not (name and email):
        raise HTTPException(status_code=400, detail="Missing fields: name and email required")

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM customers WHERE email=%s", (email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")

        cur.execute("""
            INSERT INTO customers (first_name, last_name, email)
            VALUES (%s, %s, %s) RETURNING customer_id
        """, (name, '', email))
        return {"customer_id": cur.fetchone()["customer_id"]}

@app.post("/users/login")
def login_user(data: dict):
    email = data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Missing field: email required")

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT customer_id, first_name FROM customers WHERE email=%s", (email,))
        user = cur.fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return {"customer_id": user["customer_id"], "name": user["first_name"], "message": "Login successful"}

# ----------------------
# Orders endpoints
# ----------------------
@app.post("/orders")
def create_order(data: dict):
    customer_id = data.get("customer_id")
    product_id = data.get("product_id")
    quantity = data.get("quantity")
    
    if not all([customer_id, product_id, quantity]):
        raise HTTPException(status_code=400, detail="Missing required fields: customer_id, product_id, quantity")
    
    with get_conn() as conn, conn.cursor() as cur:
        # Check if product exists and has enough stock
        cur.execute("SELECT name, price, stock FROM products WHERE product_id = %s", (product_id,))
        product = cur.fetchone()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        if product['stock'] < quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock. Available: {product['stock']}")
        
        # Create order
        cur.execute("""
            INSERT INTO orders (customer_id, order_date)
            VALUES (%s, CURRENT_DATE)
            RETURNING order_id
        """, (customer_id,))
        order = cur.fetchone()
        order_id = order['order_id']
        
        # Create order item
        cur.execute("""
            INSERT INTO order_items (order_id, product_id, quantity)
            VALUES (%s, %s, %s)
            RETURNING order_item_id
        """, (order_id, product_id, quantity))
        order_item = cur.fetchone()
        
        # Decrease product stock
        cur.execute("""
            UPDATE products
            SET stock = stock - %s
            WHERE product_id = %s
        """, (quantity, product_id))
        
        # Calculate total price
        total_price = float(product['price']) * quantity
        
        # Return order information
        return {
            "order_id": order_id,
            "customer_id": customer_id,
            "order_items": [{
                "order_item_id": order_item['order_item_id'],
                "product_id": product_id,
                "product_name": product['name'],
                "price": float(product['price']),
                "quantity": quantity,
                "total_price": total_price
            }],
            "total_price": total_price
        }

@app.get("/orders")
def list_orders(customer_id: int = None):
    with get_conn() as conn, conn.cursor() as cur:
        if customer_id:
            cur.execute("SELECT * FROM orders WHERE customer_id=%s ORDER BY order_id DESC", (customer_id,))
        else:
            cur.execute("SELECT * FROM orders ORDER BY order_id DESC")
        return cur.fetchall()

# ----------------------
# Products endpoints
# ----------------------
@app.get("/products")
def get_products():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT 
                p.product_id,
                p.name AS product_name,
                c.name AS category_name,
                p.price,
                p.stock
            FROM products p
            JOIN categories c ON p.category_id = c.category_id
            ORDER BY p.product_id
        """)
        return cur.fetchall()

# ----------------------
# Categories endpoints
# ----------------------
@app.get("/categories")
def get_categories():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT category_id, name FROM categories ORDER BY category_id")
        return cur.fetchall()

@app.get("/categories/{category_id}")
def get_category(category_id: int):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT category_id, name FROM categories WHERE category_id = %s", (category_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Category not found")
        return row

@app.post("/categories", status_code=201)
def create_category(data: dict):
    name = data.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="Missing 'name'")
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO categories (name) VALUES (%s) RETURNING category_id", (name,))
        return cur.fetchone()

# ----------------------
# Statistics endpoints
# ----------------------
@app.get("/statistics/users")
def statistics_users():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT
                c.customer_id,
                c.first_name || ' ' || c.last_name AS customer_name,
                COUNT(DISTINCT o.order_id) AS order_count,
                SUM(oi.quantity * p.price) AS total_spent
            FROM customers c
            LEFT JOIN orders o ON c.customer_id = o.customer_id
            LEFT JOIN order_items oi ON o.order_id = oi.order_id
            LEFT JOIN products p ON p.product_id = oi.product_id
            GROUP BY c.customer_id, customer_name
            ORDER BY total_spent DESC NULLS LAST
        """)
        return cur.fetchall()

@app.get("/statistics/products")
def statistics_products():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT
                p.product_id,
                p.name AS product_name,
                SUM(oi.quantity) AS order_count,
                SUM(oi.quantity * p.price) AS revenue
            FROM products p
            LEFT JOIN order_items oi ON p.product_id = oi.product_id
            GROUP BY p.product_id, p.name
            ORDER BY revenue DESC NULLS LAST
        """)
        return cur.fetchall()
