import os
import sqlite3
import json
from PIL import Image, ImageOps, ImageEnhance

DB_PATH = "ecommerce.db"
TEMPLATE_DIR = "static/templates"
IMAGE_DIR = "static/images/products"

# Category to template filename map
TEMPLATE_MAP = {
    "t-shirt": "tshirt.png",
    "polo shirt": "polo.png",
    "hoodie": "hoodie.png",
    "suit blazer": "blazer.png",
    "active joggers": "joggers.png",
    "linen shirt": "linen.png",
    "windbreaker": "windbreaker.png",
    "dress trousers": "trousers.png",
    "vintage denim jacket": "denim.png",
    "athletic shorts": "shorts.png"
}

# Color name to target RGB map (for colorizing highlights)
COLOR_MAP = {
    "red": (220, 38, 38),      # Bright Red
    "blue": (37, 99, 235),     # Royal Blue
    "green": (22, 163, 74),    # Grass Green
    "black": (45, 55, 72),     # Dark Charcoal (to represent black clothing highlights)
    "white": (245, 245, 247),  # Pure Off-White
    "grey": (148, 163, 184),   # Slate Grey
    "yellow": (234, 179, 8),   # Vibrant Yellow
    "navy": (26, 54, 110),     # Dark Navy
    "brown": (120, 53, 15),    # Earthy Brown
    "orange": (249, 115, 22)   # Sunset Orange
}

DEFAULT_COLOR = (139, 92, 246)  # Violet/Purple fallback

def colorize_product_image(template_path, output_path, target_color):
    """
    Open a gray template image, tint it with the target color (keeping shadows black),
    boost contrast/brightness for realistic texture, and save it.
    """
    try:
        # Load and convert to grayscale
        base_img = Image.open(template_path).convert("RGB")
        gray_img = ImageOps.grayscale(base_img)
        
        # Colorize: map black (0) to (0,0,0) to retain shadows/background,
        # and white (255) to target RGB.
        colorized = ImageOps.colorize(gray_img, black=(0, 0, 0), white=target_color)
        
        # Enhance contrast to make shadows pop and highlight fabric textures
        enhancer = ImageEnhance.Contrast(colorized)
        colorized = enhancer.enhance(1.15)
        
        # Save
        colorized.save(output_path, "PNG")
        return True
    except Exception as e:
        print(f"Error colorizing {template_path}: {e}")
        return False

def generate_real_product_images():
    os.makedirs(IMAGE_DIR, exist_ok=True)
    
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    
    cursor.execute("SELECT id, name, tags FROM products")
    products = cursor.fetchall()
    
    total = len(products)
    print(f"Starting photo-realistic tinting for {total} catalog products...")
    
    success_count = 0
    for index, p in enumerate(products):
        pid, name, tags_json = p
        tags = json.loads(tags_json or "[]")
        
        # Parse attributes
        p_color = "default"
        for t in tags:
            if ":" in t:
                k, v = t.split(":", 1)
                if k.strip().lower() == "color":
                    p_color = v.strip().lower()
                    break
                    
        # Match RGB target color
        target_rgb = COLOR_MAP.get(p_color, DEFAULT_COLOR)
        
        # Determine apparel category from name
        name_words = name.split()
        apparel_category = "item"
        if len(name_words) >= 3:
            apparel_category = " ".join(name_words[2:]).lower()
            
        # Match template file
        template_file = TEMPLATE_MAP.get(apparel_category, "tshirt.png")
        template_path = os.path.join(TEMPLATE_DIR, template_file)
        
        # Fallback if template doesn't exist on disk
        if not os.path.exists(template_path):
            template_path = os.path.join(TEMPLATE_DIR, "tshirt.png")
            
        # Output filename
        img_filename = f"product_{pid}.png"
        output_path = os.path.join(IMAGE_DIR, img_filename)
        
        # Execute colorization
        success = colorize_product_image(template_path, output_path, target_rgb)
        if success:
            success_count += 1
            # Update database record
            relative_url = f"/static/images/products/{img_filename}"
            cursor.execute("UPDATE products SET image_url = ? WHERE id = ?", (relative_url, pid))
            
        if (index + 1) % 250 == 0:
            print(f"Processed {index + 1}/{total} items...")
            
    db.commit()
    db.close()
    print(f"Photo-realistic imaging pipeline completed. Generated {success_count}/{total} unique product photos.")

if __name__ == "__main__":
    generate_real_product_images()
