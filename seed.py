import sqlite3
import json
import random

DB_PATH = "ecommerce.db"

def seed_database():
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    
    # 1. Clear existing data
    cursor.execute("DROP TABLE IF EXISTS order_items")
    cursor.execute("DROP TABLE IF EXISTS orders")
    cursor.execute("DROP TABLE IF EXISTS interactions")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS users")
    
    # Re-create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            preferences TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            inventory INTEGER NOT NULL,
            tags TEXT,
            image_url TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    ''')
    
    # 2. Seed Users
    users = [
        ("shopper1", "pass123", "shopper", json.dumps({"Style: Sporty": 5, "Color: Blue": 4, "Color: Red": 3, "Brand: Nike": 4, "Category: Electronics": 2})),
        ("shopper2", "pass123", "shopper", json.dumps({"Style: Casual": 5, "Color: Green": 4, "Color: White": 3, "Brand: H&M": 4, "Category: Women Ethnic": 3})),
        ("shopper3", "pass123", "shopper", json.dumps({"Style: Formal": 5, "Color: Black": 5, "Color: Grey": 4, "Brand: Apple": 5, "Category: Electronics": 5})),
        ("seller1", "pass123", "seller", None),
        ("admin1", "pass123", "admin", None),
    ]
    cursor.executemany("INSERT INTO users (username, password, role, preferences) VALUES (?, ?, ?, ?)", users)
    
    # 3. Define Item Configuration Templates
    # Category definition: (name, list of sub-types, brands, allowed_colors, allowed_sizes, allowed_styles, template_image_name_or_vector_flag)
    categories_cfg = [
        # Women
        ("Women Western", ["Dress", "Top"], ["Zara", "H&M", "Levi's", "Calvin Klein"], 
         ["Red", "Blue", "Black", "White", "Green", "Yellow", "Orange"], ["S", "M", "L", "XL"], ["Casual", "Minimalist", "Vintage", "Streetwear"], "women_western"),
         
        ("Women Ethnic", ["Saree", "Lehenga", "Kurti"], ["Biba", "Fabindia", "Manyavar"], 
         ["Red", "Yellow", "Green", "Orange", "Blue", "White"], ["M", "L", "XL", "XXL"], ["Classic", "Vintage"], "women_ethnic"),
         
        ("Women Activewear", ["Sports Bra", "Leggings"], ["Nike", "Puma", "Adidas", "Reebok"], 
         ["Black", "Navy", "Grey", "Blue", "Red"], ["S", "M", "L"], ["Sporty"], "women_active"),
         
        ("Women Sleepwear", ["Pyjamas", "Nightgown"], ["Zara", "H&M", "Calvin Klein"], 
         ["White", "Blue", "Grey", "Red", "Green"], ["S", "M", "L", "XL"], ["Casual"], "women_sleepwear"),
         
        # Men
        ("Men Western", ["T-Shirt", "Shirt", "Trousers", "Jeans", "Blazer"], ["US Polo", "Levi's", "Zara", "H&M", "Nike", "Adidas"], 
         ["White", "Black", "Blue", "Grey", "Navy", "Brown", "Orange", "Red", "Green"], ["S", "M", "L", "XL", "XXL"], ["Sporty", "Casual", "Formal", "Streetwear", "Classic"], "men_western"),
         
        ("Men Ethnic", ["Kurta", "Nehru Jacket"], ["Manyavar", "Fabindia"], 
         ["White", "Yellow", "Blue", "Orange", "Red", "Brown", "Green"], ["M", "L", "XL", "XXL"], ["Classic"], "men_ethnic"),
         
        # Kids
        ("Kids Wear", ["Casual Wear", "Kids Ethnic", "School Uniform", "School Backpack"], ["Zara", "H&M", "Fabindia", "Nike"], 
         ["Blue", "Red", "Green", "Yellow", "White", "Orange"], ["S", "M"], ["Casual", "Sporty", "Classic"], "kids_wear"),
         
        # Footwear
        ("Footwear", ["Casual Shoes", "Sneakers", "Formal Shoes", "Sandals", "Flip-Flops", "Sports Shoes"], ["Nike", "Puma", "Adidas", "Reebok", "Woodland"], 
         ["Black", "White", "Red", "Blue", "Grey", "Brown"], ["M", "L", "XL"], ["Sporty", "Casual", "Formal"], "footwear"),
         
        # Electronics
        ("Electronics", ["Smartphone", "Laptop", "Wireless Headphones", "Smartwatch", "Portable Speaker"], ["Apple", "Samsung", "Sony", "Bose", "Dell", "HP", "Xiaomi"], 
         ["Black", "Grey", "White", "Blue", "Yellow"], ["M"], ["Minimalist"], "electronics")
    ]
    
    # Generate 2000 unique products programmatically
    products = []
    random.seed(42) # Reproducible seeding
    
    for i in range(1, 2001):
        cfg = random.choice(categories_cfg)
        cat_name, sub_types, brands, colors, sizes, styles, img_type = cfg
        
        sub_type = random.choice(sub_types)
        brand = random.choice(brands)
        color = random.choice(colors)
        size = random.choice(sizes)
        style = random.choice(styles)
        
        name = f"{brand} {color} {sub_type}"
        description = f"Premium quality {sub_type} from {brand}. Designed in {style} style, size {size}."
        price = round(random.uniform(14.99, 1199.99) if sub_type == "Laptop" else random.uniform(9.99, 199.99), 2)
        inventory = random.randint(0, 100)
        
        tags = [
            f"Category: {cat_name}",
            f"Brand: {brand}",
            f"Color: {color}",
            f"Size: {size}",
            f"Style: {style}",
            f"Type: {sub_type}"
        ]
        
        # Placeholder image link (will be colorized and overwritten by generate_catalog_images_real.py)
        # Point to a temporary value
        img_url = f"/static/images/products/product_{i}.png"
        products.append((name, description, price, inventory, json.dumps(tags), img_url))
        
    cursor.executemany("INSERT INTO products (name, description, price, inventory, tags, image_url) VALUES (?, ?, ?, ?, ?, ?)", products)
    db.commit()
    
    # Fetch user ids for mapping interactions
    cursor.execute("SELECT id, username FROM users")
    user_ids = {row[1]: row[0] for row in cursor.fetchall()}
    
    # Fetch some items to seed initial interaction history
    cursor.execute("SELECT id FROM products WHERE name LIKE 'Nike%Sports Shoes' LIMIT 5")
    shoes_rows = cursor.fetchall()
    
    cursor.execute("SELECT id FROM products WHERE name LIKE 'Apple%Smartphone' LIMIT 5")
    phone_rows = cursor.fetchall()
    
    cursor.execute("SELECT id FROM products WHERE name LIKE 'Zara%Dress' LIMIT 5")
    dress_rows = cursor.fetchall()
    
    # Seed historic interaction logs
    interactions = []
    
    # shopper1 likes sports shoes
    for r in shoes_rows:
        interactions.append((user_ids["shopper1"], r[0], "view"))
        interactions.append((user_ids["shopper1"], r[0], "like"))
        
    # shopper2 likes dresses
    for r in dress_rows:
        interactions.append((user_ids["shopper2"], r[0], "view"))
        interactions.append((user_ids["shopper2"], r[0], "like"))
        
    # shopper3 likes Apple electronics
    for r in phone_rows:
        interactions.append((user_ids["shopper3"], r[0], "view"))
        interactions.append((user_ids["shopper3"], r[0], "like"))
        
    # Overlap
    if shoes_rows and phone_rows:
        interactions.append((user_ids["shopper2"], shoes_rows[0][0], "like"))
        interactions.append((user_ids["shopper1"], phone_rows[0][0], "like"))
        
    cursor.executemany("INSERT INTO interactions (user_id, product_id, type) VALUES (?, ?, ?)", interactions)
    
    # Seed historical orders
    if shoes_rows:
        cursor.execute("INSERT INTO orders (user_id, total_amount) VALUES (?, 159.98)", (user_ids["shopper1"],))
        o1_id = cursor.lastrowid
        cursor.execute("INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, 2, 79.99)", 
                       (o1_id, shoes_rows[0][0]))
                       
    if phone_rows:
        cursor.execute("INSERT INTO orders (user_id, total_amount) VALUES (?, 999.00)", (user_ids["shopper3"],))
        o2_id = cursor.lastrowid
        cursor.execute("INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, 1, 999.00)", 
                       (o2_id, phone_rows[0][0]))
                       
    db.commit()
    db.close()
    print("Database successfully scaled and seeded with 2000 products across Women, Men, Kids, Footwear, and Electronics.")

if __name__ == "__main__":
    seed_database()
