import os
import certifi
from flask import Flask, request, redirect, render_template_string, url_for, session
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "verma_pustak_2071_secure_key")

# --- DATABASE CONNECTION ---
ca = certifi.where()
client = MongoClient(
    os.environ.get("MONGO_URI"),
    tlsCAFile=ca,
    tlsAllowInvalidCertificates=True,
    connect=False,
    serverSelectionTimeoutMS=5000
)
db = client['verma_pustak_db']
# We use .get_collection to prevent crashes if they don't exist yet
inventory_col = db.get_collection('inventory')
reviews_col = db.get_collection('reviews')
leads_col = db.get_collection('leads')
settings_col = db.get_collection('settings')

# --- CLOUDINARY CONFIG ---
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
        "announcement": "📢 Welcome to Verma Pustak Pasal!",
        "map_html": "Map loading...",
        "logo_url": "https://via.placeholder.com/150",
        "group_link": "#"
    }
    try:
        s = settings_col.find_one({"type": "general"})
        if s:
            return s
    except:
        pass
    return default

# --- ALL FEATURES UI ---
SITE_CSS = '''
<style>
    :root { --p: #2c3e50; --s: #25d366; --bg: #f8fafd; --card: #fff; --text: #333; }
    [data-theme="dark"] { --p: #1a1a1a; --bg: #121212; --card: #1e1e1e; --text: #fff; }
    body { background: var(--bg); color: var(--text); font-family: sans-serif; margin: 0; transition: 0.3s; }
    .announcement { background: var(--s); color: white; padding: 10px; text-align: center; font-weight: bold; }
    .header { background: var(--p); color: white; padding: 30px; text-align: center; }
    .section-card { background: var(--card); border-radius: 12px; padding: 20px; margin: 20px auto; max-width: 800px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
    .prod-card { background: var(--card); border-radius: 10px; padding: 15px; text-align: center; border: 1px solid rgba(0,0,0,0.05); margin-bottom: 20px; }
    .theme-toggle { position: fixed; top: 10px; right: 10px; z-index: 1000; cursor: pointer; }
</style>
'''

@app.route('/')
def home():
    settings = get_settings()
    inventory = list(inventory_col.find().sort("date_added", -1))
    reviews = list(reviews_col.find().sort("date", -1).limit(5))

    items_html = "".join([f'''
        <div class="col-md-4">
            <div class="prod-card">
                <img src="{p['img']}" style="height:150px; object-fit:contain; width:100%;">
                <h5 class="mt-2">{p['name']}</h5>
                <p class="text-success fw-bold">Rs. {p['price']}</p>
                <a href="https://wa.me/{settings['phone']}" class="btn btn-success btn-sm w-100">Order</a>
            </div>
        </div>''' for p in inventory])

    return render_template_string(f'''
    <!DOCTYPE html>
    <html lang="en" data-theme="light">
    <head><meta name="viewport" content="width=device-width, initial-scale=1"><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">{SITE_CSS}</head>
    <body>
        <button class="theme-toggle btn btn-sm btn-light" onclick="toggleTheme()">🌓 Theme</button>
        <div class="announcement">{settings['announcement']}</div>
        <header class="header">
            <h1>{settings['shop_name']}</h1>
            <p>Parasi, Nepal | {settings['phone']}</p>
        </header>
        <div class="container">
            <div class="section-card text-center">
                <form action="/subscribe" method="POST" class="row g-2 justify-content-center">
                    <div class="col-8"><input name="p" class="form-control" placeholder="WhatsApp Number" required></div>
                    <div class="col-4"><button class="btn btn-dark w-100">JOIN</button></div>
                </form>
            </div>
            <div class="row">{items_html if items_html else "<p class='text-center'>No books added yet.</p>"}</div>
        </div>
        <footer class="text-center p-4 mt-4 bg-dark text-white">
            <p>© 2026 {settings['shop_name']} | <a href="/admin" class="text-white">Admin Login</a></p>
        </footer>
        <script>
            function toggleTheme() {{
                const b = document.documentElement;
                const t = b.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
                b.setAttribute('data-theme', t);
                localStorage.setItem('theme', t);
            }}
            document.documentElement.setAttribute('data-theme', localStorage.getItem('theme') || 'light');
        </script>
    </body>
    </html>
    ''')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        if request.method == 'POST' and request.form.get('password') == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        return '<div style="text-align:center; margin-top:100px;"><form method="POST"><h2>Admin</h2><input type="password" name="password"><button>Login</button></form></div>'
    
    settings = get_settings()
    inventory = list(inventory_col.find())
    
    return render_template_string(f'''
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <div class="container mt-4">
        <h2>Admin Dashboard</h2><a href="/logout">Logout</a><hr>
        <div class="row">
            <div class="col-md-6">
                <form action="/update-settings" method="POST" class="card p-3 mb-3">
                    <h5>Settings</h5>
                    <input name="shop_name" value="{settings['shop_name']}" class="form-control mb-2">
                    <input name="phone" value="{settings['phone']}" class="form-control mb-2">
                    <textarea name="announcement" class="form-control mb-2">{settings['announcement']}</textarea>
                    <button class="btn btn-success w-100">Save</button>
                </form>
            </div>
            <div class="col-md-6">
                <form action="/add-product" method="POST" enctype="multipart/form-data" class="card p-3">
                    <h5>Add Book</h5>
                    <input name="n" placeholder="Book Name" class="form-control mb-2" required>
                    <input name="p" placeholder="Price" class="form-control mb-2" required>
                    <input type="file" name="file" class="form-control mb-2" required>
                    <button class="btn btn-primary w-100">Upload</button>
                </form>
            </div>
        </div>
    </div>
    ''')

@app.route('/update-settings', methods=['POST'])
def update_settings():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    settings_col.update_one({"type": "general"}, {"$set": {
        "shop_name": request.form.get('shop_name'),
        "phone": request.form.get('phone'),
        "announcement": request.form.get('announcement')
    }}, upsert=True)
    return redirect(url_for('admin'))

@app.route('/add-product', methods=['POST'])
def add_product():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    res = cloudinary.uploader.upload(request.files['file'])
    inventory_col.insert_one({
        "name": request.form.get('n'),
        "price": request.form.get('p'),
        "img": res['secure_url'],
        "date_added": datetime.now()
    })
    return redirect(url_for('admin'))

@app.route('/subscribe', methods=['POST'])
def subscribe():
    leads_col.insert_one({"phone": request.form.get('p'), "date": datetime.now()})
    return redirect("/")

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
