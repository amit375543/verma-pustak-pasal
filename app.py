import os
import certifi
from flask import Flask, request, redirect, render_template_string, url_for, session
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "verma_pustak_2071_secure")

# --- OPTIMIZED DATABASE CONNECTION ---
try:
    ca = certifi.where()
    # Adding timeouts (MS) prevents the "infinite loading" spin
    client = MongoClient(
        os.environ.get("MONGO_URI"),
        tlsCAFile=ca,
        tlsAllowInvalidCertificates=True,
        connect=False, # Connect only when needed to save memory
        serverSelectionTimeoutMS=5000, # Give up after 5 seconds instead of 30
        socketTimeoutMS=5000
    )
    db = client['verma_pustak_db']
    inventory_col = db['inventory']
    reviews_col = db['reviews']
    leads_col = db['leads']
    settings_col = db['settings']
except Exception as e:
    print(f"Database Initialization Error: {e}")

# --- CLOUDINARY CONFIGURATION ---
cloudinary.config(
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key = os.environ.get("CLOUDINARY_API_KEY"),
    api_secret = os.environ.get("CLOUDINARY_API_SECRET")
)

ADMIN_PASSWORD = "verma@123"
CATEGORIES = ["Textbooks", "Stationery", "Calculators", "Other"]

def get_settings():
    default = {
        "shop_name": "Verma Pustak Pasal",
        "phone": "9847299546",
        "fb_url": "https://facebook.com/vermapustakpasal",
        "announcement": "📢 Welcome to Verma Pustak Pasal!",
        "map_html": "Map loading...",
        "logo_url": "https://via.placeholder.com/150",
        "group_link": "#"
    }
    try:
        s = settings_col.find_one({"type": "general"})
        return s if s else default
    except:
        return default

# --- MINIMAL CSS ---
SITE_CSS = '''
<style>
    :root { --p: #2c3e50; --s: #25d366; --bg: #f8fafd; --txt: #333; }
    body { background: var(--bg); color: var(--txt); font-family: sans-serif; margin: 0; }
    .nav { background: var(--p); color: white; padding: 20px; text-align: center; }
    .announcement { background: var(--s); color: white; padding: 8px; text-align: center; font-size: 0.9rem; font-weight: bold; }
    .card { background: white; border-radius: 10px; padding: 15px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .btn-wa { background: var(--s); color: white; text-decoration: none; padding: 10px; border-radius: 5px; display: block; text-align: center; font-weight: bold; }
    .footer { background: var(--p); color: white; padding: 20px; text-align: center; margin-top: 40px; }
    img { max-width: 100%; border-radius: 8px; }
</style>
'''

@app.route('/')
def home():
    settings = get_settings()
    selected_cat = request.args.get('category', 'All')
    
    try:
        query = {} if selected_cat == "All" else {"cat": selected_cat}
        inventory = list(inventory_col.find(query).limit(20)) # Limit results for speed
        reviews = list(reviews_col.find().sort("date", -1).limit(5))
    except:
        inventory, reviews = [], []

    items_html = "".join([f'''
        <div class="card">
            <img src="{p['img']}" style="height:150px; object-fit:contain;">
            <h4 style="margin:10px 0 5px 0;">{p['name']}</h4>
            <p style="color:var(--p); font-weight:bold;">Rs. {p['price']}</p>
            <a href="https://wa.me/{settings['phone']}?text=Hi, I want {p['name']}" class="btn-wa">Order on WhatsApp</a>
        </div>''' for p in inventory])

    return render_template_string(f'''
    <!DOCTYPE html>
    <html>
    <head><meta name="viewport" content="width=device-width, initial-scale=1">{SITE_CSS}</head>
    <body>
        <div class="announcement">{settings['announcement']}</div>
        <div class="nav">
            <h1>{settings['shop_name']}</h1>
            <p>Parasi, Nepal | {settings['phone']}</p>
        </div>
        <div style="padding: 20px; max-width: 800px; margin: auto;">
            <div style="text-align:center; margin-bottom:20px;">
                <a href="/">All</a> | 
                <a href="/?category=Textbooks">Textbooks</a> | 
                <a href="/?category=Stationery">Stationery</a>
            </div>
            {items_html if items_html else "<p>Loading products...</p>"}
        </div>
        <div class="footer">
            <p>© 2026 {settings['shop_name']} | <a href="/admin" style="color:white;">Admin Panel</a></p>
        </div>
    </body>
    </html>
    ''')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        if request.method == 'POST' and request.form.get('password') == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        return '<form method="POST" style="text-align:center; margin-top:100px;"><h2>Admin Login</h2><input type="password" name="password"><button>Login</button></form>'

    return render_template_string(f'''
    <div style="max-width:600px; margin:auto; padding:20px; font-family:sans-serif;">
        <h2>Admin Dashboard</h2>
        <a href="/logout">Logout</a><hr>
        <form action="/add-product" method="POST" enctype="multipart/form-data">
            <h3>Add Product</h3>
            <input name="n" placeholder="Product Name" required><br><br>
            <input name="p" placeholder="Price" required><br><br>
            <select name="cat"><option>Textbooks</option><option>Stationery</option></select><br><br>
            <input type="file" name="file" required><br><br>
            <button style="background:blue; color:white; padding:10px;">Upload to Shop</button>
        </form>
    </div>
    ''')

@app.route('/add-product', methods=['POST'])
def add_product():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    try:
        res = cloudinary.uploader.upload(request.files['file'])
        inventory_col.insert_one({
            "name": request.form.get('n'),
            "price": request.form.get('p'),
            "cat": request.form.get('cat'),
            "img": res['secure_url'],
            "date_added": datetime.now()
        })
    except Exception as e:
        print(f"Upload error: {e}")
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    # Force port to 10000 for Render compatibility
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
