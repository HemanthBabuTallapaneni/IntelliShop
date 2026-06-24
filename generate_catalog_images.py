import os
import sqlite3
import json
from PIL import Image, ImageDraw, ImageFont

DB_PATH = "ecommerce.db"
IMAGE_DIR = "static/images/products"

# Color mappings to RGB color tuples
COLOR_PALETTES = {
    "red": {"bg_start": (59, 7, 18), "bg_end": (185, 28, 28), "text": (254, 226, 226)},
    "blue": {"bg_start": (3, 7, 18), "bg_end": (29, 78, 216), "text": (219, 234, 254)},
    "green": {"bg_start": (2, 44, 34), "bg_end": (4, 120, 87), "text": (209, 250, 229)},
    "black": {"bg_start": (9, 13, 22), "bg_end": (31, 41, 55), "text": (243, 244, 246)},
    "white": {"bg_start": (15, 23, 42), "bg_end": (203, 213, 225), "text": (255, 255, 255)},
    "grey": {"bg_start": (17, 24, 39), "bg_end": (75, 85, 99), "text": (243, 244, 246)},
    "yellow": {"bg_start": (66, 32, 6), "bg_end": (180, 83, 9), "text": (254, 243, 199)}, # gold/yellow
    "navy": {"bg_start": (2, 6, 23), "bg_end": (30, 58, 138), "text": (239, 246, 255)},
    "brown": {"bg_start": (28, 25, 23), "bg_end": (120, 53, 15), "text": (255, 247, 237)},
    "orange": {"bg_start": (42, 12, 10), "bg_end": (194, 65, 12), "text": (255, 237, 213)}
}

DEFAULT_PALETTE = {"bg_start": (11, 15, 25), "bg_end": (49, 46, 129), "text": (243, 244, 246)}

def draw_gradient_background(draw, width, height, start_color, end_color):
    """Draw a smooth diagonal linear gradient."""
    for y in range(height):
        # Calculate interpolation factor
        ratio = y / height
        # Interpolate color channels
        r = int(start_color[0] * (1 - ratio) + end_color[0] * ratio)
        g = int(start_color[1] * (1 - ratio) + end_color[1] * ratio)
        b = int(start_color[2] * (1 - ratio) + end_color[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

def draw_apparel_silhouette(draw, width, height, category, accent_color):
    """Draw a stylized abstract outline of the clothing item."""
    center_x = width // 2
    center_y = height // 2
    
    # Stylized clothing contours using PIL basic shapes
    if category in ("t-shirt", "polo shirt", "linen shirt"):
        # Torso rectangle
        draw.rectangle([center_x - 50, center_y - 20, center_x + 50, center_y + 80], outline=accent_color, width=3)
        # Left sleeve
        draw.polygon([
            (center_x - 50, center_y - 20),
            (center_x - 80, center_y),
            (center_x - 65, center_y + 15),
            (center_x - 50, center_y + 5)
        ], outline=accent_color, width=3)
        # Right sleeve
        draw.polygon([
            (center_x + 50, center_y - 20),
            (center_x + 80, center_y),
            (center_x + 65, center_y + 15),
            (center_x + 50, center_y + 5)
        ], outline=accent_color, width=3)
        # Neck collar line
        draw.arc([center_x - 20, center_y - 30, center_x + 20, center_y - 10], start=0, end=180, fill=accent_color, width=3)
        
    elif category == "hoodie":
        # Body
        draw.rectangle([center_x - 55, center_y - 10, center_x + 55, center_y + 70], outline=accent_color, width=3)
        # Sleeves
        draw.line([(center_x - 55, center_y - 10), (center_x - 80, center_y + 50)], fill=accent_color, width=3)
        draw.line([(center_x + 55, center_y - 10), (center_x + 80, center_y + 50)], fill=accent_color, width=3)
        # Hood outline
        draw.ellipse([center_x - 30, center_y - 45, center_x + 30, center_y - 15], outline=accent_color, width=3)
        
    elif category == "suit blazer":
        # Shoulder rectangle
        draw.rectangle([center_x - 55, center_y - 20, center_x + 55, center_y + 80], outline=accent_color, width=3)
        # Lapels (V neck)
        draw.line([(center_x - 55, center_y - 20), (center_x, center_y + 30)], fill=accent_color, width=3)
        draw.line([(center_x + 55, center_y - 20), (center_x, center_y + 30)], fill=accent_color, width=3)
        # Tie outline
        draw.polygon([(center_x - 8, center_y - 5), (center_x + 8, center_y - 5), (center_x, center_y + 20)], fill=accent_color)
        
    elif category == "active joggers" or category == "dress trousers":
        # Left Leg
        draw.rectangle([center_x - 40, center_y - 30, center_x - 10, center_y + 80], outline=accent_color, width=3)
        # Right Leg
        draw.rectangle([center_x + 10, center_y - 30, center_x + 40, center_y + 80], outline=accent_color, width=3)
        # Waist band
        draw.line([(center_x - 40, center_y - 30), (center_x + 40, center_y - 30)], fill=accent_color, width=4)
        
    elif category == "vintage denim jacket" or category == "windbreaker":
        # Body
        draw.rectangle([center_x - 55, center_y - 20, center_x + 55, center_y + 70], outline=accent_color, width=3)
        # Zipper line
        draw.line([(center_x, center_y - 20), (center_x, center_y + 70)], fill=accent_color, width=2)
        # Left/Right collar flaps
        draw.polygon([(center_x - 30, center_y - 20), (center_x - 10, center_y - 20), (center_x - 20, center_y - 5)], outline=accent_color, width=2)
        draw.polygon([(center_x + 30, center_y - 20), (center_x + 10, center_y - 20), (center_x + 20, center_y - 5)], outline=accent_color, width=2)
        
    elif category == "athletic shorts":
        # Left leg
        draw.rectangle([center_x - 45, center_y - 20, center_x - 5, center_y + 30], outline=accent_color, width=3)
        # Right leg
        draw.rectangle([center_x + 5, center_y - 20, center_x + 45, center_y + 30], outline=accent_color, width=3)
        # Waistband
        draw.line([(center_x - 45, center_y - 20), (center_x + 45, center_y - 20)], fill=accent_color, width=4)
        
    else:
        # Default placeholder geometric icon
        draw.regular_polygon(((center_x, center_y + 20), 45), 6, rotation=0, outline=accent_color, width=3)

def generate_unique_images():
    os.makedirs(IMAGE_DIR, exist_ok=True)
    
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    
    cursor.execute("SELECT id, name, tags FROM products")
    products = cursor.fetchall()
    
    total = len(products)
    print(f"Generating {total} unique images...")
    
    # Try loading default font, otherwise fallback
    try:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    except Exception:
        font_large = None
        font_small = None
        
    for index, p in enumerate(products):
        pid, name, tags_json = p
        tags = json.loads(tags_json or "[]")
        
        # 1. Parse attributes from tags
        p_color = "default"
        p_brand = "Generic"
        p_style = "Casual"
        p_size = "M"
        
        for t in tags:
            if ":" in t:
                k, v = t.split(":", 1)
                k, v = k.strip().lower(), v.strip()
                if k == "color": p_color = v.lower()
                elif k == "brand": p_brand = v
                elif k == "style": p_style = v
                elif k == "size": p_size = v
                
        # 2. Match color palette
        palette = COLOR_PALETTES.get(p_color, DEFAULT_PALETTE)
        
        # Extract apparel category
        # Product names look like: "Nike Red T-Shirt"
        name_words = name.split()
        apparel_category = "item"
        if len(name_words) >= 3:
            # Join words after brand & color
            apparel_category = " ".join(name_words[2:]).lower()
            
        # 3. Create canvas
        width, height = 400, 400
        image = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(image)
        
        # Draw background gradient
        draw_gradient_background(draw, width, height, palette["bg_start"], palette["bg_end"])
        
        # Draw tech circular grid detail (glow effect)
        draw.ellipse([width//2 - 120, height//2 - 100, width//2 + 120, height//2 + 140], outline=(255,255,255,10), width=1)
        draw.ellipse([width//2 - 122, height//2 - 102, width//2 + 122, height//2 + 142], outline=(255,255,255,5), width=1)
        
        # Draw product category silhouette
        silhouette_color = palette["text"]
        draw_apparel_silhouette(draw, width, height, apparel_category, silhouette_color)
        
        # Draw brand label at the top
        draw.text((20, 20), p_brand.upper(), fill=silhouette_color)
        
        # Draw size & style metadata at the top-right
        metadata_text = f"{p_style.upper()} / {p_size}"
        draw.text((width - 120, 20), metadata_text, fill=silhouette_color)
        
        # Draw product short code at the bottom-left
        draw.text((20, height - 35), f"#PROD-{pid:04d}", fill=silhouette_color)
        
        # Draw product type text at bottom-right
        draw.text((width - 150, height - 35), apparel_category.title(), fill=silhouette_color)
        
        # 4. Save image
        img_filename = f"product_{pid}.png"
        img_path = os.path.join(IMAGE_DIR, img_filename)
        image.save(img_path, "PNG")
        
        # 5. Mutate database image URL
        relative_url = f"/static/images/products/{img_filename}"
        cursor.execute("UPDATE products SET image_url = ? WHERE id = ?", (relative_url, pid))
        
        if (index + 1) % 250 == 0:
            print(f"Generated {index + 1}/{total} product images...")
            
    db.commit()
    db.close()
    print("Programmatic image pipeline completed successfully. 1500 unique product images generated.")

if __name__ == "__main__":
    generate_unique_images()
