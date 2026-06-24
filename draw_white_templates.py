import os
from PIL import Image, ImageDraw, ImageOps

TEMPLATE_DIR = "static/templates"
os.makedirs(TEMPLATE_DIR, exist_ok=True)

def create_base_canvas(width, height):
    # Create a clean, modern dark charcoal gradient background
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)
    
    # Smooth vertical dark gradient (from dark slate to slightly lighter charcoal)
    for y in range(height):
        ratio = y / height
        # Slate black (15, 23, 42) to dark charcoal (31, 41, 55)
        r = int(15 * (1 - ratio) + 31 * ratio)
        g = int(23 * (1 - ratio) + 41 * ratio)
        b = int(42 * (1 - ratio) + 55 * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
        
    # Draw a subtle circular tech grid background (light glow)
    draw.ellipse([width//2 - 300, height//2 - 250, width//2 + 300, height//2 + 350], outline=(255, 255, 255, 10), width=2)
    draw.ellipse([width//2 - 305, height//2 - 255, width//2 + 305, height//2 + 355], outline=(255, 255, 255, 5), width=1)
    
    return image, draw

def save_template(image, filename):
    path = os.path.join(TEMPLATE_DIR, filename)
    image.save(path, "PNG")
    print(f"Created white template: {path}")

def draw_white_footwear():
    # 1024x1024 canvas
    width, height = 1024, 1024
    image, draw = create_base_canvas(width, height)
    center_x = width // 2
    center_y = height // 2
    
    # Coordinates scaled up by ~2.56 from 400x400
    # Sole (light grey/white)
    sole_points = [
        (center_x - 230, center_y + 100),
        (center_x + 230, center_y + 115),
        (center_x + 243, center_y + 90),
        (center_x + 154, center_y + 72),
        (center_x - 179, center_y + 67),
        (center_x - 243, center_y + 77)
    ]
    draw.polygon(sole_points, fill=(235, 235, 235))
    
    # Sole grooves
    for gx in range(center_x - 200, center_x + 200, 38):
        draw.line([(gx, center_y + 90), (gx - 13, center_y + 110)], fill=(150, 150, 150), width=5)
        
    # Main Shoe Body Panel (pure white fabric)
    body_points = [
        (center_x - 230, center_y + 64),
        (center_x - 205, center_y - 13),
        (center_x - 102, center_y - 51),
        (center_x, center_y - 115),       # ankle collar back
        (center_x + 90, center_y - 102),  # ankle collar front
        (center_x + 77, center_y - 38),   # tongue area
        (center_x + 205, center_y + 51),  # toe box top
        (center_x + 230, center_y + 72),  # toe box front
        (center_x - 230, center_y + 64)
    ]
    draw.polygon(body_points, fill=(255, 255, 255), outline=(200, 200, 200), width=5)
    
    # Ankle cushioning collar overlay
    draw.ellipse([center_x - 38, center_y - 123, center_x + 82, center_y - 77], outline=(220, 220, 220), width=5)
    
    # Mesh side panels
    draw.polygon([
        (center_x - 102, center_y + 13),
        (center_x + 26, center_y + 13),
        (center_x + 102, center_y + 51),
        (center_x - 51, center_y + 51)
    ], outline=(200, 200, 200), width=3)
    
    # Lacing lines
    draw.line([(center_x + 26, center_y - 77), (center_x + 64, center_y - 38)], fill=(220, 220, 220), width=8)
    draw.line([(center_x + 38, center_y - 59), (center_x + 77, center_y - 20)], fill=(220, 220, 220), width=8)
    draw.line([(center_x + 51, center_y - 38), (center_x + 90, center_y)], fill=(220, 220, 220), width=8)
    
    save_template(image, "footwear.png")

def draw_white_laptop():
    width, height = 1024, 1024
    image, draw = create_base_canvas(width, height)
    center_x = width // 2
    center_y = height // 2
    
    # Laptop Screen Bezel (silver/white)
    draw.rectangle([center_x - 256, center_y - 154, center_x + 256, center_y + 77], outline=(240, 240, 240), width=10, fill=(30, 30, 30))
    # Laptop Screen Content (pure white glowing center)
    draw.rectangle([center_x - 241, center_y - 138, center_x + 241, center_y + 61], fill=(255, 255, 255))
    # Screen inner wallpaper details (subtle concentric circles in light silver)
    draw.ellipse([center_x - 50, center_y - 50, center_x + 50, center_y + 50], outline=(220, 220, 220), width=3)
    
    # Laptop Base (metallic silver/white keyboard area)
    draw.polygon([
        (center_x - 307, center_y + 90),
        (center_x + 307, center_y + 90),
        (center_x + 256, center_y + 141),
        (center_x - 256, center_y + 141)
    ], fill=(230, 230, 230), outline=(255, 255, 255), width=5)
    
    # Trackpad outline
    draw.rectangle([center_x - 64, center_y + 102, center_x + 64, center_y + 128], outline=(180, 180, 180), width=3)
    
    save_template(image, "laptop.png")

def draw_white_smartphone():
    width, height = 1024, 1024
    image, draw = create_base_canvas(width, height)
    center_x = width // 2
    center_y = height // 2
    
    # Phone Body Bezel (white/silver frame)
    draw.rounded_rectangle([center_x - 140, center_y - 243, center_x + 140, center_y + 243], radius=30, fill=(20, 20, 20), outline=(255, 255, 255), width=10)
    
    # Phone Screen (pure white screen)
    draw.rounded_rectangle([center_x - 125, center_y - 228, center_x + 125, center_y + 228], radius=20, fill=(255, 255, 255))
    
    # Camera notch/speaker (dark)
    draw.rounded_rectangle([center_x - 38, center_y - 225, center_x + 38, center_y - 205], radius=10, fill=(20, 20, 20))
    
    # App icons / details on screen (subtle grey grid)
    for row in range(-128, 154, 77):
        for col in range(-77, 102, 51):
            draw.ellipse([center_x + col - 12, center_y + row - 12, center_x + col + 12, center_y + row + 12], fill=(230, 230, 230))
            
    save_template(image, "smartphone.png")

def draw_white_saree():
    width, height = 1024, 1024
    image, draw = create_base_canvas(width, height)
    center_x = width // 2
    center_y = height // 2
    
    # Main Saree Fabric Body (flowing folds in pure white)
    fabric_points = [
        (center_x - 100, center_y - 154),
        (center_x + 100, center_y - 154),
        (center_x + 166, center_y + 218),
        (center_x - 166, center_y + 218),
        (center_x - 100, center_y - 154)
    ]
    draw.polygon(fabric_points, fill=(255, 255, 255), outline=(220, 220, 220), width=5)
    
    # Fold lines (drapery shadows)
    draw.line([(center_x - 50, center_y - 154), (center_x - 80, center_y + 218)], fill=(200, 200, 200), width=4)
    draw.line([(center_x, center_y - 154), (center_x - 10, center_y + 218)], fill=(200, 200, 200), width=4)
    draw.line([(center_x + 50, center_y - 154), (center_x + 60, center_y + 218)], fill=(200, 200, 200), width=4)
    
    # Silver Border (zari border represented as pure white/silver details)
    border_color = (240, 240, 240)
    draw.polygon([
        (center_x - 169, center_y + 179),
        (center_x + 169, center_y + 179),
        (center_x + 172, center_y + 223),
        (center_x - 172, center_y + 223)
    ], fill=border_color, outline=(255, 255, 255), width=2)
    
    # Diagonal pallu sash
    sash_points = [
        (center_x - 102, center_y - 128),
        (center_x - 26, center_y - 102),
        (center_x + 166, center_y + 179),
        (center_x + 115, center_y + 205),
        (center_x - 102, center_y - 128)
    ]
    draw.polygon(sash_points, fill=(255, 255, 255), outline=border_color, width=4)
    
    save_template(image, "saree.png")

def draw_white_kurta():
    width, height = 1024, 1024
    image, draw = create_base_canvas(width, height)
    center_x = width // 2
    center_y = height // 2
    
    # Kurta Tunic body (pure white)
    fabric_points = [
        (center_x - 102, center_y - 154),
        (center_x + 102, center_y - 154),
        (center_x + 166, center_y + 218),
        (center_x - 166, center_y + 218),
        (center_x - 102, center_y - 154)
    ]
    draw.polygon(fabric_points, fill=(255, 255, 255), outline=(220, 220, 220), width=5)
    
    # Placket and button details (silver/white)
    draw.rectangle([center_x - 10, center_y - 128, center_x + 10, center_y], fill=(240, 240, 240))
    # Pocket outline
    draw.rectangle([center_x - 38, center_y - 51, center_x - 13, center_y - 26], outline=(200, 200, 200), width=3)
    
    # Neckline collar arc
    draw.arc([center_x - 51, center_y - 179, center_x + 51, center_y - 115], start=0, end=180, fill=(240, 240, 240), width=8)
    
    save_template(image, "kurta.png")

def draw_white_kids():
    width, height = 1024, 1024
    image, draw = create_base_canvas(width, height)
    center_x = width // 2
    center_y = height // 2
    
    # Cute kids casual apparel (small shirt and shorts silhouette, pure white)
    # Shirt
    draw.rectangle([center_x - 100, center_y - 150, center_x + 100, center_y + 20], fill=(255, 255, 255), outline=(220, 220, 220), width=5)
    # Sleeves
    draw.polygon([(center_x - 100, center_y - 150), (center_x - 150, center_y - 80), (center_x - 100, center_y - 50)], fill=(255, 255, 255), outline=(220, 220, 220), width=3)
    draw.polygon([(center_x + 100, center_y - 150), (center_x + 150, center_y - 80), (center_x + 100, center_y - 50)], fill=(255, 255, 255), outline=(220, 220, 220), width=3)
    
    # Shorts
    draw.rectangle([center_x - 90, center_y + 30, center_x - 10, center_y + 180], fill=(255, 255, 255), outline=(220, 220, 220), width=5)
    draw.rectangle([center_x + 10, center_y + 30, center_x + 90, center_y + 180], fill=(255, 255, 255), outline=(220, 220, 220), width=5)
    # Waistband connector
    draw.rectangle([center_x - 90, center_y + 20, center_x + 90, center_y + 40], fill=(240, 240, 240))
    
    save_template(image, "kids.png")

def draw_white_backpack():
    width, height = 1024, 1024
    image, draw = create_base_canvas(width, height)
    center_x = width // 2
    center_y = height // 2
    
    # Backpack Main Body (pure white canvas)
    draw.rounded_rectangle([center_x - 115, center_y - 180, center_x + 115, center_y + 180], radius=30, fill=(255, 255, 255), outline=(220, 220, 220), width=5)
    
    # Front pocket
    draw.rounded_rectangle([center_x - 77, center_y + 26, center_x + 77, center_y + 154], radius=10, fill=(245, 245, 245), outline=(200, 200, 200), width=3)
    
    # Zipper lines
    draw.line([(center_x - 115, center_y - 90), (center_x + 115, center_y - 90)], fill=(180, 180, 180), width=4)
    draw.line([(center_x - 77, center_y + 40), (center_x + 77, center_y + 40)], fill=(180, 180, 180), width=4)
    
    # Carry handle at top
    draw.arc([center_x - 38, center_y - 218, center_x + 38, center_y - 179], start=180, end=360, fill=(220, 220, 220), width=8)
    
    save_template(image, "backpack.png")

def generate_all_white_templates():
    print("Generating custom white-on-dark templates...")
    draw_white_footwear()
    draw_white_laptop()
    draw_white_smartphone()
    draw_white_saree()
    draw_white_kurta()
    draw_white_kids()
    draw_white_backpack()
    print("All custom white templates successfully created!")

if __name__ == "__main__":
    generate_all_white_templates()
