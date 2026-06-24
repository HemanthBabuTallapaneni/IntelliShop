import os
import urllib.request

TEMPLATE_DIR = "static/templates"
os.makedirs(TEMPLATE_DIR, exist_ok=True)

# Clean, high-quality, license-free base product images from Unsplash (400x400)
TEMPLATES_TO_DOWNLOAD = {
    "smartphone.png": "https://images.unsplash.com/photo-1598327105666-5b89351aff97?auto=format&fit=crop&w=400&h=400&q=80",
    "laptop.png": "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?auto=format&fit=crop&w=400&h=400&q=80",
    "footwear.png": "https://images.unsplash.com/photo-1608231387042-66d1773070a5?auto=format&fit=crop&w=400&h=400&q=80",
    "saree.png": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?auto=format&fit=crop&w=400&h=400&q=80",
    "kurta.png": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?auto=format&fit=crop&w=400&h=400&q=80",
    "kids.png": "https://images.unsplash.com/photo-1503919545889-aef636e10ad4?auto=format&fit=crop&w=400&h=400&q=80",
    "backpack.png": "https://images.unsplash.com/photo-1581605405669-fcdf81165afa?auto=format&fit=crop&w=400&h=400&q=80"
}

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

def download_assets():
    print("Downloading base product photo templates...")
    for filename, url in TEMPLATES_TO_DOWNLOAD.items():
        dest_path = os.path.join(TEMPLATE_DIR, filename)
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response, open(dest_path, 'wb') as out_file:
                out_file.write(response.read())
            print(f"Downloaded: {filename}")
        except Exception as e:
            print(f"Failed to download {filename} from {url}: {e}")

if __name__ == "__main__":
    download_assets()
