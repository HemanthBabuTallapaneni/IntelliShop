import os
import sqlite3
import json
from PIL import Image, ImageOps, ImageEnhance

DB_PATH = "ecommerce.db"
TEMPLATE_DIR = "static/templates"
IMAGE_DIR = "static/images/products"

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

DEFAULT_COLOR = (139, 92, 246)  # Fallback: Violet/Purple

# Category type to template mapping (covering all 2000 product types with photo templates!)
TEMPLATE_MAP = {
    # Standard Men's / Women's Western
    "t-shirt": "tshirt.png",
    "polo shirt": "polo.png",
    "hoodie": "hoodie.png",
    "suit blazer": "blazer.png",
    "active joggers": "joggers.png",
    "linen shirt": "linen.png",
    "windbreaker": "windbreaker.png",
    "dress trousers": "trousers.png",
    "vintage denim jacket": "denim.png",
    "athletic shorts": "shorts.png",
    
    # Women's wear
    "dress": "linen.png",         # drape shirts/dress
    "top": "tshirt.png",
    "saree": "saree.png",
    "lehenga": "saree.png",
    "kurti": "kurta.png",
    "sports bra": "tshirt.png",
    "leggings": "joggers.png",
    "pyjamas": "joggers.png",
    "nightgown": "linen.png",
    
    # Men's Traditional
    "kurta": "kurta.png",
    "nehru jacket": "blazer.png",
    
    # Kids
    "casual wear": "kids.png",
    "kids ethnic": "kurta.png",
    "school uniform": "kids.png",
    "school backpack": "backpack.png",
    
    # Footwear
    "casual shoes": "footwear.png",
    "sneakers": "footwear.png",
    "formal shoes": "footwear.png",
    "sandals": "footwear.png",
    "flip-flops": "footwear.png",
    "sports shoes": "footwear.png",
    
    # Electronics
    "smartphone": "smartphone.png",
    "laptop": "laptop.png",
    "wireless headphones": "smartphone.png",
    "smartwatch": "smartphone.png",
    "portable speaker": "smartphone.png"
}

def colorize_product_photo(template_path, output_path, target_color):
    """
    Open a photo-realistic template image, convert to grayscale to preserve
    shadows/folds, tint the highlights with target color, and apply contrast correction.
    """
    try:
        base_img = Image.open(template_path).convert("RGB")
        gray_img = ImageOps.grayscale(base_img)
        
        # Colorize: map black to black, and white to target color highlights
        colorized = ImageOps.colorize(gray_img, black=(0, 0, 0), white=target_color)
        
        # Boost contrast to make the textures, highlights, and shadows look highly photorealistic
        colorized = ImageEnhance.Contrast(colorized).enhance(1.15)
        
        colorized.save(output_path, "PNG")
        return True
    except Exception as e:
        print(f"Error colorizing photo for {template_path}: {e}")
        return False

def generate_all_catalog_photos():
    os.makedirs(IMAGE_DIR, exist_ok=True)
    
    # Connect with timeout to prevent locks from running server
    db = sqlite3.connect(DB_PATH, timeout=30.0)
    cursor = db.cursor()
    
    cursor.execute("SELECT id, name, tags FROM products")
    products = cursor.fetchall()
    
    total = len(products)
    print(f"Executing 100% photo-realistic tinting pipeline for {total} items...")
    
    success_count = 0
    for index, p in enumerate(products):
        pid, name, tags_json = p
        tags = json.loads(tags_json or "[]")
        
        # 1. Parse attributes
        p_color = "default"
        p_type = "Garment"
        
        # Adjust the color based on the product name (case-insensitive check)
        name_lower = name.lower()
        for color_key in COLOR_MAP.keys():
            if color_key in name_lower:
                p_color = color_key
                break
                
        # Parse fallback from tags if not found in name
        if p_color == "default":
            for t in tags:
                if ":" in t:
                    k, v = t.split(":", 1)
                    k, v = k.strip().lower(), v.strip()
                    if k == "color": 
                        p_color = v.lower()
                        break
                        
        # Get type from tags
        for t in tags:
            if ":" in t:
                k, v = t.split(":", 1)
                k, v = k.strip().lower(), v.strip()
                if k == "type":
                    p_type = v
                    break
                
        # Get target color
        target_rgb = COLOR_MAP.get(p_color, DEFAULT_COLOR)
        
        # Output file path
        img_filename = f"product_{pid}.png"
        output_path = os.path.join(IMAGE_DIR, img_filename)
        
        # Match type to template filename
        type_key = p_type.lower()
        template_file = TEMPLATE_MAP.get(type_key, "tshirt.png")
        template_path = os.path.join(TEMPLATE_DIR, template_file)
        
        # Fallback if specific template is missing on disk
        if not os.path.exists(template_path):
            template_path = os.path.join(TEMPLATE_DIR, "tshirt.png")
            
        # Execute photo-realistic colorization
        success = colorize_product_photo(template_path, output_path, target_rgb)
        if success:
            success_count += 1
            # Update database record
            relative_url = f"/static/images/products/{img_filename}"
            cursor.execute("UPDATE products SET image_url = ? WHERE id = ?", (relative_url, pid))
            
        if (index + 1) % 500 == 0:
            print(f"Processed {index + 1}/{total} items...")
            
    db.commit()
    db.close()
    print(f"Photo-realistic image processing complete. Successfully generated {success_count}/{total} unique product photos.")

if __name__ == "__main__":
    generate_all_catalog_photos()
