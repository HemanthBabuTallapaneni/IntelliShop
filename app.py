import os
import json
import sqlite3
import math
import base64
import hashlib
import hmac
import time
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, g

app = Flask(__name__)
app.secret_key = "antigravity_super_secret_session_key"
app.jinja_env.globals.update(json_loads=json.loads)

DB_PATH = "ecommerce.db"
if os.environ.get("VERCEL"):
    import shutil
    tmp_db = "/tmp/ecommerce.db"
    if not os.path.exists(tmp_db) and os.path.exists("ecommerce.db"):
        shutil.copy("ecommerce.db", tmp_db)
    DB_PATH = tmp_db

JWT_SECRET = "orchestration_engine_secure_key_12345"

# --- DATABASE CONNECTION HELPER ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- INITIALIZE DATABASE ---
def init_db():
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    
    # Create Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL, -- 'shopper', 'seller', 'admin'
            preferences TEXT -- JSON string for content preference vectors
        )
    ''')
    
    # Create Products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            inventory INTEGER NOT NULL,
            tags TEXT, -- JSON array of tags, e.g. ["Color: Red", "Brand: US Polo", "Style: Slim Fit", "Size: M"]
            image_url TEXT
        )
    ''')
    
    # Create Interactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            type TEXT NOT NULL, -- 'view', 'like', 'cart'
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    ''')
    
    # Create Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Create Order Items table
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
    
    db.commit()
    db.close()

# --- JWT SIMULATOR ---
def base64url_encode(data):
    if isinstance(data, dict):
        data = json.dumps(data)
    encoded = base64.urlsafe_b64encode(data.encode('utf-8')).decode('utf-8')
    return encoded.replace('=', '')

def base64url_decode(data):
    padding = '=' * (4 - len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode('utf-8')).decode('utf-8')

def generate_jwt(user_id, username, role):
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": int(time.time()) + 3600
    }
    
    unsigned_token = f"{base64url_encode(header)}.{base64url_encode(payload)}"
    signature = hmac.new(
        JWT_SECRET.encode('utf-8'),
        unsigned_token.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    encoded_signature = base64.urlsafe_b64encode(signature).decode('utf-8').replace('=', '')
    return f"{unsigned_token}.{encoded_signature}"

def verify_jwt(token):
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        unsigned_token = f"{parts[0]}.{parts[1]}"
        expected_sig = hmac.new(
            JWT_SECRET.encode('utf-8'),
            unsigned_token.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        encoded_sig = base64.urlsafe_b64encode(expected_sig).decode('utf-8').replace('=', '')
        if not hmac.compare_digest(parts[2], encoded_sig):
            return None
            
        payload = json.loads(base64url_decode(parts[1]))
        if payload.get("exp", 0) < time.time():
            return None
            
        return payload
    except Exception:
        return None

# JWT Middleware decorator for Flask
def token_required(allowed_roles=None):
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def decorated(*args, **kwargs):
            token = session.get("jwt_token") or request.headers.get("Authorization")
            if token and token.startswith("Bearer "):
                token = token.split(" ")[1]
            
            is_json_request = (
                request.path.startswith("/shopper/product/") or 
                request.path.startswith("/shopper/like/") or 
                request.path.startswith("/shopper/cart/") or
                "application/json" in request.headers.get("Accept", "")
            )
            
            if not token:
                if is_json_request:
                    return jsonify({"error": "Authentication required. Please sign in."}), 401
                if request.path.startswith("/shopper"):
                    return redirect(url_for("shopper_login", next=request.url))
                elif request.path.startswith("/seller"):
                    return redirect(url_for("seller_login", next=request.url))
                return redirect(url_for("login_page", next=request.url))
                
            payload = verify_jwt(token)
            if not payload:
                session.pop("jwt_token", None)
                if is_json_request:
                    return jsonify({"error": "Session expired or invalid token."}), 401
                if request.path.startswith("/shopper"):
                    return redirect(url_for("shopper_login", error="Session expired."))
                elif request.path.startswith("/seller"):
                    return redirect(url_for("seller_login", error="Session expired."))
                return redirect(url_for("login_page", error="Session expired or invalid token."))
                
            if allowed_roles and payload["role"] not in allowed_roles:
                if is_json_request:
                    return jsonify({"error": "Forbidden: Access denied."}), 403
                return render_template("unauthorized.html", error=f"Access Denied: Requires {', '.join(allowed_roles)} role.")
                
            # Store in flask g
            g.user = payload
            g.jwt_token = token
            return f(*args, **kwargs)
        return decorated
    return decorator


# --- RECOMMENDER SYSTEM ENGINE ---

def get_user_behavior_matrix():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT user_id, product_id, type FROM interactions")
    rows = cursor.fetchall()
    
    # Structure: user_likes = { user_id: {product_id_1, product_id_2} }
    user_likes = {}
    for r in rows:
        uid = r["user_id"]
        pid = r["product_id"]
        itype = r["type"]
        if itype in ("like", "cart"):
            user_likes.setdefault(uid, set()).add(pid)
    return user_likes

def collaborative_filtering(user_id, user_likes, num_recs=4):
    """
    Predict product affinity using statistical similarities between user matrices.
    Using Jaccard Similarity: |Intersection| / |Union|
    """
    target_likes = user_likes.get(user_id, set())
    if not target_likes:
        return {} # Can't do collaborative filtering without target user history
        
    user_similarities = {}
    for other_id, other_likes in user_likes.items():
        if other_id == user_id:
            continue
        intersection = target_likes.intersection(other_likes)
        union = target_likes.union(other_likes)
        if union:
            user_similarities[other_id] = len(intersection) / len(union)
            
    # Calculate weighted product score
    product_scores = {}
    for other_id, similarity in user_similarities.items():
        if similarity <= 0:
            continue
        for pid in user_likes[other_id]:
            if pid not in target_likes: # Only recommend new items
                product_scores[pid] = product_scores.get(pid, 0) + similarity
                
    return product_scores

def compute_cosine_similarity(vec1, vec2):
    dot_product = sum(vec1.get(tag, 0) * vec2.get(tag, 0) for tag in vec1)
    mag1 = math.sqrt(sum(val**2 for val in vec1.values()))
    mag2 = math.sqrt(sum(val**2 for val in vec2.values()))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot_product / (mag1 * mag2)

def content_based_filtering(user_id, target_likes, num_recs=4):
    """
    Calculate cosine similarity between user preference vectors and product tags.
    """
    db = get_db()
    cursor = db.cursor()
    
    # 1. Build user preference vector from liked items
    user_vector = {}
    if target_likes:
        placeholders = ','.join('?' for _ in target_likes)
        cursor.execute(f"SELECT tags FROM products WHERE id IN ({placeholders})", list(target_likes))
        liked_tags_rows = cursor.fetchall()
        for r in liked_tags_rows:
            tags = json.loads(r["tags"] or "[]")
            for t in tags:
                user_vector[t] = user_vector.get(t, 0) + 1 # weight is occurrence count
    else:
        # Fallback to general user preferences if saved in database
        cursor.execute("SELECT preferences FROM users WHERE id = ?", (user_id,))
        pref_row = cursor.fetchone()
        if pref_row and pref_row["preferences"]:
            user_vector = json.loads(pref_row["preferences"])

    if not user_vector:
        return {} # No preferences established yet
        
    # 2. Fetch candidate products not already liked
    cursor.execute("SELECT id, tags FROM products")
    all_products = cursor.fetchall()
    
    scores = {}
    for p in all_products:
        pid = p["id"]
        if pid in target_likes:
            continue
        
        p_tags = json.loads(p["tags"] or "[]")
        # Build binary product vector
        product_vector = {tag: 1.0 for tag in p_tags}
        
        # Cosine similarity
        sim = compute_cosine_similarity(user_vector, product_vector)
        if sim > 0:
            scores[pid] = sim
            
    return scores

def get_hybrid_recommendations(user_id, num_recs=4):
    db = get_db()
    cursor = db.cursor()
    
    # Get user interaction history
    user_likes = get_user_behavior_matrix()
    target_likes = user_likes.get(user_id, set())
    
    # 1. Collaborative Filtering Scores
    cf_scores = collaborative_filtering(user_id, user_likes, num_recs)
    
    # 2. Content-Based Scores
    cb_scores = content_based_filtering(user_id, target_likes, num_recs)
    
    # 3. Catalog Popularity (prior checkout weights)
    cursor.execute("SELECT product_id, SUM(quantity) as sales FROM order_items GROUP BY product_id")
    popularity = {r["product_id"]: float(r["sales"]) for r in cursor.fetchall()}
    max_popularity = max(popularity.values()) if popularity else 1.0
    
    # Combine scores
    hybrid_scores = []
    cursor.execute("SELECT id, name, description, price, inventory, tags, image_url FROM products")
    products = cursor.fetchall()
    
    for p in products:
        pid = p["id"]
        # Skip if inventory is depleted or already liked
        if p["inventory"] <= 0 or pid in target_likes:
            continue
            
        cf = cf_scores.get(pid, 0.0)
        cb = cb_scores.get(pid, 0.0)
        pop = popularity.get(pid, 0.0) / max_popularity
        
        # Hybrid formula weighting: 50% Content, 30% Collaborative, 20% Popularity
        hybrid_score = (0.50 * cb) + (0.30 * cf) + (0.20 * pop)
        
        hybrid_scores.append({
            "product": p,
            "score": round(hybrid_score, 4),
            "breakdown": {
                "content_cb": round(cb, 2),
                "collab_cf": round(cf, 2),
                "popularity": round(pop, 2)
            }
        })
        
    # Sort by hybrid score descending
    hybrid_scores.sort(key=lambda x: x["score"], reverse=True)
    return hybrid_scores[:num_recs]

# --- DYNAMIC INDEXING & SEARCH ENGINE ---

def dynamic_search_index(query_text, tag_filters=None):
    """
    Search index matching text tokens against dynamic attribute tags and product name/description.
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, name, description, tags, price, inventory, image_url FROM products")
    products = cursor.fetchall()
    
    query_tokens = [tok.lower().strip() for tok in query_text.split() if tok.strip()]
    results = []
    
    for p in products:
        p_tags = json.loads(p["tags"] or "[]")
        p_tags_lower = [t.lower() for t in p_tags]
        
        # Check text match
        text_score = 0
        name_desc = (p["name"] + " " + (p["description"] or "")).lower()
        
        # If query is provided, match tokens
        if query_tokens:
            for token in query_tokens:
                if token in name_desc:
                    text_score += 2.0
                for tag in p_tags_lower:
                    if token in tag:
                        text_score += 3.0
        else:
            text_score = 1.0 # Baseline match when query is empty

        # If tag filters are selected, they MUST match (AND behavior for filters)
        filter_match = True
        if tag_filters:
            for category, val in tag_filters.items():
                if val:
                    expected_tag = f"{category.lower()}: {val.lower()}"
                    if not any(expected_tag in t.lower() for t in p_tags_lower):
                        filter_match = False
                        break
                        
        if filter_match and text_score > 0:
            results.append({
                "product": p,
                "score": text_score,
                "tags": p_tags
            })
            
    # Sort results by match score descending, then by inventory
    results.sort(key=lambda x: (x["score"], x["product"]["inventory"]), reverse=True)
    return results

# --- ANALYTICS PIPELINE ---

def get_seller_analytics():
    db = get_db()
    cursor = db.cursor()
    
    # 1. Total revenue & orders count
    cursor.execute("SELECT SUM(total_amount) as rev, COUNT(id) as cnt FROM orders")
    res = cursor.fetchone()
    total_revenue = res["rev"] or 0.0
    total_orders = res["cnt"] or 0
    
    # 2. Product performance (Sales numbers, inventory health)
    cursor.execute('''
        SELECT p.id, p.name, p.inventory, COALESCE(SUM(oi.quantity), 0) as sold, COALESCE(SUM(oi.quantity * oi.price), 0.0) as revenue
        FROM products p
        LEFT JOIN order_items oi ON p.id = oi.product_id
        GROUP BY p.id
    ''')
    product_stats = cursor.fetchall()
    
    # 3. User views vs. likes conversion rates
    cursor.execute('''
        SELECT 
            p.id, 
            p.name,
            COUNT(CASE WHEN i.type = 'view' THEN 1 END) as views,
            COUNT(CASE WHEN i.type = 'like' THEN 1 END) as likes,
            COUNT(CASE WHEN i.type = 'cart' THEN 1 END) as carts
        FROM products p
        LEFT JOIN interactions i ON p.id = i.product_id
        GROUP BY p.id
    ''')
    conversion_stats = []
    for r in cursor.fetchall():
        views = r["views"] or 0
        likes = r["likes"] or 0
        conversion = (likes / views * 100) if views > 0 else 0.0
        conversion_stats.append({
            "id": r["id"],
            "name": r["name"],
            "views": views,
            "likes": likes,
            "carts": r["carts"] or 0,
            "conversion_rate": round(conversion, 1)
        })
        
    # 4. Sales Trends (orders over time)
    cursor.execute('''
        SELECT strftime('%Y-%m-%d %H:%M', timestamp) as time_slot, SUM(total_amount) as amount 
        FROM orders 
        GROUP BY time_slot 
        ORDER BY time_slot DESC 
        LIMIT 10
    ''')
    trends = [{"time": r["time_slot"], "amount": r["amount"]} for r in cursor.fetchall()]
    
    return {
        "revenue": round(total_revenue, 2),
        "orders_count": total_orders,
        "product_stats": product_stats,
        "conversion_stats": conversion_stats,
        "trends": list(reversed(trends))
    }

# --- ROUTES ---

@app.route("/")
def home():
    user = None
    if "jwt_token" in session:
        payload = verify_jwt(session["jwt_token"])
        if payload:
            user = payload
    return render_template("landing.html", user=user)

@app.route("/shopper/login", methods=["GET", "POST"])
def shopper_login():
    if "jwt_token" in session:
        payload = verify_jwt(session["jwt_token"])
        if payload and payload["role"] == "shopper":
            return redirect(url_for("shopper_dashboard"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ? AND role = ?", (email, password, "shopper"))
        user = cursor.fetchone()
        
        if user:
            token = generate_jwt(user["id"], user["username"], user["role"])
            session["jwt_token"] = token
            return redirect(url_for("shopper_dashboard"))
        else:
            return render_template("shopper_login.html", error="Invalid email or password.")
            
    return render_template("shopper_login.html")

@app.route("/shopper/register", methods=["GET", "POST"])
def shopper_register():
    if "jwt_token" in session:
        payload = verify_jwt(session["jwt_token"])
        if payload and payload["role"] == "shopper":
            return redirect(url_for("shopper_dashboard"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (email,))
        if cursor.fetchone():
            return render_template("shopper_register.html", error="Email already registered.")
            
        cursor.execute("INSERT INTO users (username, password, role, preferences) VALUES (?, ?, ?, ?)",
                       (email, password, "shopper", json.dumps({})))
        db.commit()
        
        # Log in newly registered user
        cursor.execute("SELECT * FROM users WHERE username = ?", (email,))
        user = cursor.fetchone()
        token = generate_jwt(user["id"], user["username"], user["role"])
        session["jwt_token"] = token
        return redirect(url_for("shopper_dashboard"))
        
    return render_template("shopper_register.html")

@app.route("/seller/login", methods=["GET", "POST"])
def seller_login():
    if "jwt_token" in session:
        payload = verify_jwt(session["jwt_token"])
        if payload and payload["role"] == "seller":
            return redirect(url_for("seller_dashboard"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ? AND role = ?", (email, password, "seller"))
        user = cursor.fetchone()
        
        if user:
            token = generate_jwt(user["id"], user["username"], user["role"])
            session["jwt_token"] = token
            return redirect(url_for("seller_dashboard"))
        else:
            return render_template("seller_login.html", error="Invalid email or password.")
            
    return render_template("seller_login.html")

@app.route("/seller/register", methods=["GET", "POST"])
def seller_register():
    if "jwt_token" in session:
        payload = verify_jwt(session["jwt_token"])
        if payload and payload["role"] == "seller":
            return redirect(url_for("seller_dashboard"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (email,))
        if cursor.fetchone():
            return render_template("seller_register.html", error="Email already registered.")
            
        cursor.execute("INSERT INTO users (username, password, role, preferences) VALUES (?, ?, ?, ?)",
                       (email, password, "seller", None))
        db.commit()
        
        # Log in newly registered user
        cursor.execute("SELECT * FROM users WHERE username = ?", (email,))
        user = cursor.fetchone()
        token = generate_jwt(user["id"], user["username"], user["role"])
        session["jwt_token"] = token
        return redirect(url_for("seller_dashboard"))
        
    return render_template("seller_register.html")

@app.route("/social-login", methods=["POST"])
def social_login():
    provider = request.form.get("provider")
    role = request.form.get("role")
    
    # Generate mock email and password
    email = f"{provider}_{role}@example.com"
    password = "mock_social_login_password_2026"
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (email,))
    user = cursor.fetchone()
    
    if not user:
        # Create user if they don't exist yet
        prefs = json.dumps({}) if role == "shopper" else None
        cursor.execute("INSERT INTO users (username, password, role, preferences) VALUES (?, ?, ?, ?)",
                       (email, password, role, prefs))
        db.commit()
        cursor.execute("SELECT * FROM users WHERE username = ?", (email,))
        user = cursor.fetchone()
        
    token = generate_jwt(user["id"], user["username"], user["role"])
    session["jwt_token"] = token
    
    if role == "shopper":
        return redirect(url_for("shopper_dashboard"))
    elif role == "seller":
        return redirect(url_for("seller_dashboard"))
        
    return redirect(url_for("home"))

@app.route("/login", methods=["GET", "POST"])
def login_page():
    # Keep the legacy login page route for compatibility (e.g. admin logins or pre-seeded credentials)
    db = get_db()
    cursor = db.cursor()
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        
        if user:
            token = generate_jwt(user["id"], user["username"], user["role"])
            session["jwt_token"] = token
            return redirect(url_for("home"))
        else:
            cursor.execute("SELECT username, password, role FROM users")
            demo_users = cursor.fetchall()
            return render_template("login.html", error="Invalid username or password.", demo_users=demo_users)
            
    cursor.execute("SELECT username, password, role FROM users")
    demo_users = cursor.fetchall()
    return render_template("login.html", demo_users=demo_users)

@app.route("/logout")
def logout():
    session.pop("jwt_token", None)
    session.pop("cart", None)
    return redirect(url_for("home"))


# --- SHOPPER DASHBOARD ---
@app.route("/shopper")
@token_required(allowed_roles=["shopper", "admin"])
def shopper_dashboard():
    db = get_db()
    cursor = db.cursor()
    
    user_id = g.user["user_id"]
    
    query = request.args.get("query", "")
    color = request.args.get("color", "")
    brand = request.args.get("brand", "")
    size = request.args.get("size", "")
    style = request.args.get("style", "")
    
    tag_filters = {
        "Color": color,
        "Brand": brand,
        "Size": size,
        "Style": style
    }
    
    # 2. Get search results or full inventory (slice top 124 for page load performance)
    search_results = dynamic_search_index(query, tag_filters)[:124]
    
    # 3. Fetch Hybrid Recommendations in real-time
    recommendations = get_hybrid_recommendations(user_id, num_recs=4)
    
    # 4. Fetch Cart Contents from session
    cart = session.get("cart", {})
    cart_items = []
    cart_total = 0.0
    
    if cart:
        placeholders = ','.join('?' for _ in cart.keys())
        cursor.execute(f"SELECT * FROM products WHERE id IN ({placeholders})", list(cart.keys()))
        products = cursor.fetchall()
        for p in products:
            qty = cart[str(p["id"])]
            subtotal = p["price"] * qty
            cart_total += subtotal
            cart_items.append({
                "id": p["id"],
                "name": p["name"],
                "price": p["price"],
                "quantity": qty,
                "inventory": p["inventory"],
                "subtotal": round(subtotal, 2)
            })
            
    # Get distinct attribute tag lists for filter dropdown UI elements
    cursor.execute("SELECT tags FROM products")
    all_tags = cursor.fetchall()
    
    unique_attributes = {"Color": set(), "Brand": set(), "Size": set(), "Style": set()}
    for row in all_tags:
        tags = json.loads(row["tags"] or "[]")
        for t in tags:
            if ":" in t:
                k, v = t.split(":", 1)
                k, v = k.strip(), v.strip()
                if k in unique_attributes:
                    unique_attributes[k].add(v)
                    
    # Log view interaction for recommendations
    if not query and not any(tag_filters.values()):
        for rec in recommendations:
            pid = rec["product"]["id"]
            cursor.execute("INSERT INTO interactions (user_id, product_id, type) VALUES (?, ?, 'view')", (user_id, pid))
        db.commit()

    return render_template(
        "shopper.html",
        user=g.user,
        jwt_token=g.jwt_token,
        recommendations=recommendations,
        products=search_results,
        cart_items=cart_items,
        cart_total=round(cart_total, 2),
        attributes=unique_attributes,
        active_filters=tag_filters,
        active_query=query,
        success=request.args.get("success"),
        error=request.args.get("error")
    )

@app.route("/shopper/product/<int:product_id>")
@token_required(allowed_roles=["shopper", "admin"])
def get_product_details(product_id):
    db = get_db()
    cursor = db.cursor()
    
    # 1. Fetch product
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    p = cursor.fetchone()
    if not p:
        return jsonify({"error": "Product not found"}), 404
        
    # Log view interaction for recommendation training
    user_id = g.user["user_id"]
    cursor.execute("INSERT INTO interactions (user_id, product_id, type) VALUES (?, ?, 'view')", (user_id, product_id))
    db.commit()
    
    # 2. Get similar products (Cosine Similarity between product tags)
    p_tags = json.loads(p["tags"] or "[]")
    target_vector = {t: 1.0 for t in p_tags}
    
    cursor.execute("SELECT id, name, price, inventory, tags, image_url FROM products WHERE id != ?", (product_id,))
    candidates = cursor.fetchall()
    
    similarities = []
    for c in candidates:
        c_tags = json.loads(c["tags"] or "[]")
        c_vector = {t: 1.0 for t in c_tags}
        sim = compute_cosine_similarity(target_vector, c_vector)
        if sim > 0:
            similarities.append({
                "id": c["id"],
                "name": c["name"],
                "price": c["price"],
                "inventory": c["inventory"],
                "image_url": c["image_url"],
                "similarity": round(sim, 2)
            })
            
    # Sort by similarity descending, then by inventory
    similarities.sort(key=lambda x: (x["similarity"], x["inventory"]), reverse=True)
    top_similar = similarities[:4]
    
    # Extract properties from tags for quick UI access
    extracted_props = {}
    for t in p_tags:
        if ":" in t:
            k, v = t.split(":", 1)
            extracted_props[k.strip()] = v.strip()
            
    return jsonify({
        "id": p["id"],
        "name": p["name"],
        "description": p["description"],
        "price": p["price"],
        "inventory": p["inventory"],
        "image_url": p["image_url"],
        "tags": p_tags,
        "attributes": extracted_props,
        "similar_products": top_similar
    })

@app.route("/shopper/like/<int:product_id>", methods=["POST"])
@token_required(allowed_roles=["shopper", "admin"])
def like_product(product_id):
    db = get_db()
    cursor = db.cursor()
    user_id = g.user["user_id"]
    
    # Log like interaction
    cursor.execute("INSERT INTO interactions (user_id, product_id, type) VALUES (?, ?, 'like')", (user_id, product_id))
    
    # Mutate User preference vector
    cursor.execute("SELECT tags FROM products WHERE id = ?", (product_id,))
    p_row = cursor.fetchone()
    if p_row:
        p_tags = json.loads(p_row["tags"] or "[]")
        
        cursor.execute("SELECT preferences FROM users WHERE id = ?", (user_id,))
        u_row = cursor.fetchone()
        prefs = json.loads(u_row["preferences"] or "{}")
        
        for tag in p_tags:
            prefs[tag] = prefs.get(tag, 0) + 2
            
        cursor.execute("UPDATE users SET preferences = ? WHERE id = ?", (json.dumps(prefs), user_id))
        
    db.commit()
    return jsonify({"status": "success", "message": "Product liked successfully."})

@app.route("/shopper/cart/add/<int:product_id>", methods=["POST"])
@token_required(allowed_roles=["shopper", "admin"])
def add_to_cart(product_id):
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT inventory, name FROM products WHERE id = ?", (product_id,))
    p = cursor.fetchone()
    if not p or p["inventory"] <= 0:
        return jsonify({"status": "error", "message": "Item out of stock!"}), 400
        
    cart = session.get("cart", {})
    str_pid = str(product_id)
    cart[str_pid] = cart.get(str_pid, 0) + 1
    session["cart"] = cart
    
    # Log interaction
    cursor.execute("INSERT INTO interactions (user_id, product_id, type) VALUES (?, ?, 'cart')", (g.user["user_id"], product_id))
    db.commit()
    
    return jsonify({"status": "success", "message": f"{p['name']} added to cart."})

@app.route("/shopper/cart/clear", methods=["POST"])
@token_required(allowed_roles=["shopper", "admin"])
def clear_cart():
    session.pop("cart", None)
    return redirect(url_for("shopper_dashboard"))

@app.route("/shopper/checkout", methods=["POST"])
@token_required(allowed_roles=["shopper", "admin"])
def checkout():
    db = get_db()
    cursor = db.cursor()
    user_id = g.user["user_id"]
    cart = session.get("cart", {})
    
    if not cart:
        return redirect(url_for("shopper_dashboard", error="Cart is empty."))
        
    # Verify stock and calculate total
    total_amount = 0.0
    order_items = []
    
    for pid_str, qty in cart.items():
        pid = int(pid_str)
        cursor.execute("SELECT id, name, price, inventory FROM products WHERE id = ?", (pid,))
        p = cursor.fetchone()
        if not p or p["inventory"] < qty:
            return redirect(url_for("shopper_dashboard", error=f"Insufficient inventory for item: {p['name'] if p else 'Unknown'}"))
            
        subtotal = p["price"] * qty
        total_amount += subtotal
        order_items.append((pid, qty, p["price"]))
        
    # Mutation 1: Create Order
    cursor.execute("INSERT INTO orders (user_id, total_amount) VALUES (?, ?)", (user_id, total_amount))
    order_id = cursor.lastrowid
    
    # Mutation 2: Create Order Items & Mutate Inventory Health instantly
    for pid, qty, price in order_items:
        cursor.execute("INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)", 
                       (order_id, pid, qty, price))
        cursor.execute("UPDATE products SET inventory = inventory - ? WHERE id = ?", (qty, pid))
        
    db.commit()
    session.pop("cart", None) # empty cart
    
    return redirect(url_for("shopper_dashboard", success=f"Order #{order_id} placed successfully! Total: ${total_amount:.2f}"))


# --- SELLER DASHBOARD ---
@app.route("/seller", methods=["GET", "POST"])
@token_required(allowed_roles=["seller", "admin"])
def seller_dashboard():
    db = get_db()
    cursor = db.cursor()
    
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "add":
            name = request.form.get("name")
            desc = request.form.get("description")
            price = float(request.form.get("price"))
            inventory = int(request.form.get("inventory"))
            img = request.form.get("image_url")
            
            # Reconstruct attributes
            color = request.form.get("color")
            brand = request.form.get("brand")
            size = request.form.get("size")
            style = request.form.get("style")
            
            tags = []
            if color: tags.append(f"Color: {color}")
            if brand: tags.append(f"Brand: {brand}")
            if size: tags.append(f"Size: {size}")
            if style: tags.append(f"Style: {style}")
            
            cursor.execute(
                "INSERT INTO products (name, description, price, inventory, tags, image_url) VALUES (?, ?, ?, ?, ?, ?)",
                (name, desc, price, inventory, json.dumps(tags), img)
            )
            db.commit()
            
        elif action == "update_stock":
            pid = int(request.form.get("product_id"))
            new_stock = int(request.form.get("inventory"))
            
            cursor.execute("UPDATE products SET inventory = ? WHERE id = ?", (new_stock, pid))
            db.commit()
            
        return redirect(url_for("seller_dashboard"))
        
    analytics = get_seller_analytics()
    return render_template("seller.html", user=g.user, jwt_token=g.jwt_token, analytics=analytics)


# --- ADMIN DASHBOARD ---
@app.route("/admin", methods=["GET", "POST"])
@token_required(allowed_roles=["admin"])
def admin_dashboard():
    db = get_db()
    cursor = db.cursor()
    
    if request.method == "POST":
        action = request.form.get("action")
        if action == "update_role":
            uid = int(request.form.get("user_id"))
            new_role = request.form.get("role")
            cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, uid))
            db.commit()
        return redirect(url_for("admin_dashboard"))
        
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    
    cursor.execute("SELECT * FROM orders ORDER BY timestamp DESC")
    orders = cursor.fetchall()
    
    return render_template(
        "admin.html",
        user=g.user,
        jwt_token=g.jwt_token,
        users=users,
        products=products,
        orders=orders
    )

# --- BOOTSTRAP SYSTEM ---
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
