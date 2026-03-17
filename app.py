import os
import certifi
from flask import Flask, request, redirect, render_template_string, url_for, session
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "verma_pustak_2026_final_fix")

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

def get_settings():
    default = {
        "type": "general",
        "shop_name": "Verma Pustak Pasal",
        "phone": "9847299546",
        "announcement": "📢 Welcome to Verma Pustak Pasal!",
        "map_html": "Map will appear after you update it in Admin.",
        "logo_url": "https://via.placeholder.com/150",
        "group_link": "#"
    }
    try:
        s = settings_col.find_one({"type": "general"})
        if not s:
            settings_col.insert_one(default)
            return default
        return s
    except:
        return default

# --- STYLING ---
SITE_CSS = '''
<style>
    :root { --p: #2c3e50; --s: #25d366; --bg: #f8fafd; --card: #fff; --text: #333; }
    body { background: var(--bg); color: var(--text); font-family: sans-serif; margin: 0; }
    .announcement { background: var(--s); color: white; padding: 12px; text-align: center; font-weight: bold; }
    .header { background: var(--p); color: white; padding: 30px; text-align: center; }
    .section-card { background: var(--card); border-radius: 12px; padding: 25px; margin: 20px auto; max-width: 800px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
    .prod-card { background: var(--card); border-radius: 10px; padding: 15px; text-align: center; border: 1px solid rgba(0,0,0,0.05); margin-bottom: 20px; }
</style>
'''

@app.route('/')
def home():
    settings = get_settings()
    try:
        inventory = list(inventory_col.find().sort("date_added", -1))
        reviews = list(reviews_col.find().sort("date", -1).limit(5))
    except:
        inventory, reviews = [], []

    items_html = "".join([f'''
        <div style="width: 30%; display: inline-block; vertical-align: top; padding: 10px;">
            <div class="prod-card shadow-sm">
                <img src="{p.get('img', '')}" style="height:150px; object-fit:contain; width:100%;">
                <h5 class="mt-2">{p.get('name', 'Book')}</h5>
                <p class="text-success fw-bold">Rs. {p.get('price', '0')}</p>
                <a href="https://wa.me/{settings['phone']}?text=I want to order {p.get('name')}" style="background:#25d366; color:white; padding:5px 10px; text-decoration:none; border-radius:5px;">Order</a>
            </div>
        </div>''' for p in inventory])

    rev_html = "".join([f'<div style="border-bottom:1px solid #ddd; padding:5px;"><strong>{r.get("name", "User")}</strong>: {r.get("msg", "")}</div>' for r in reviews])

    return render_template_string(f'''
    <!DOCTYPE html>
    <html lang="en">
    <head><meta name="viewport" content="width=device-width, initial-scale=1"><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">{SITE_CSS}</head>
    <body>
        <div class="announcement">{settings.get('announcement')}</div>
        <header class="header">
            <h1>{settings.get('shop_name')}</h1>
            <p>Ramgram-3, Parasi | 📞 {settings.get('phone')}</p>
        </header>
        <div class="container" style="padding: 20px; text-align: center;">
            <div class="section-card">
                <form action="/subscribe" method="POST">
                    <input name="p" placeholder="WhatsApp Number" required style="padding:10px; width:60%;">
                    <button type="submit" style="padding:10px; background:#2c3e50; color:white;">JOIN GROUP</button>
                </form>
            </div>
            <div style="max-width: 1000px; margin: auto;">{items_html if items_html else "<p>No products yet. Use /admin to add them!</p>"}</div>
            
            <div style="margin-top:50px; display:flex; text-align:left; flex-wrap: wrap;">
                <div style="flex:1; min-width:300px; padding:20px;">
                    <h4>Location 📍</h4>
                    <div style="border:1px solid #ddd;">{settings.get('map_html')}</div>
                </div>
                <div style="flex:1; min-width:300px; padding:20px;">
                    <h4>Customer Reviews</h4>
                    <div style="margin-bottom:20px;">{rev_html if rev_html else "No reviews yet."}</div>
                    <form action="/submit-review" method="POST" class="border p-2">
                        <input name="rev_name" placeholder="Name" required class="form-control mb-1">
                        <textarea name="rev_msg" placeholder="Review" required class="form-control mb-1"></textarea>
                        <button type="submit" class="btn btn-dark btn-sm">Post</button>
                    </form>
                </div>
            </div>
        </div>
        <footer style="text-align:center; padding:20px; background:#2c3e50; color:white; margin-top:50px;">
            <p>© 2026 {settings.get('shop_name')} | <a href="/admin" style="color:white;">Admin Login</a></p>
        </footer>
    </body>
    </html>
    ''')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        if request.method == 'POST' and request.form.get('password') == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        return '<div style="text-align:center; margin-top:100px;"><form method="POST"><h2>Admin Access</h2><input type="password" name="password" style="padding:10px;"><button style="padding:10px;">Login</button></form></div>'
    
    settings = get_settings()
    leads = list(leads_col.find().sort("date", -1))
    lead_rows = "".join([f"<tr><td>{l.get('phone')}</td><td>{l.get('date').strftime('%Y-%m-%d')}</td></tr>" for l in leads])

    return render_template_string(f'''
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <div class="container py-4">
        <h2>Admin Dashboard</h2><a href="/logout">Logout</a><hr>
        <div class="row">
            <div class="col-md-6 border-end">
                <h4>Shop Settings</h4>
                <form action="/update-settings" method="POST">
                    <label>Shop Name</label><input name="shop_name" value="{settings.get('shop_name')}" class="form-control mb-2">
                    <label>WhatsApp</label><input name="phone" value="{settings.get('phone')}" class="form-control mb-2">
                    <label>Announcement</label><textarea name="announcement" class="form-control mb-2">{settings.get('announcement')}</textarea>
                    <label>Map HTML</label><textarea name="map_html" class="form-control mb-2">{settings.get('map_html')}</textarea>
                    <button class="btn btn-success w-100">Update Shop</button>
                </form>
            </div>
            <div class="col-md-6">
                <h4>Add Product</h4>
                <form action="/add-product" method="POST" enctype="multipart/form-data">
                    <input name="n" placeholder="Book Name" class="form-control mb-2" required>
                    <input name="p" placeholder="Price" class="form-control mb-2" required>
                    <input type="file" name="file" class="form-control mb-2" required>
                    <button class="btn btn-primary w-100">Add to Stock</button>
                </form>
                <h4 class="mt-4">WhatsApp Leads</h4>
                <table class="table table-sm"><tr><th>Phone</th><th>Date</th></tr>{lead_rows}</table>
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
        "announcement": request.form.get('announcement'),
        "map_html": request.form.get('map_html')
    }}, upsert=True)
    return redirect(url_for('admin'))

@app.route('/add-product', methods=['POST'])
def add_product():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    try:
        res = cloudinary.uploader.upload(request.files['file'])
        inventory_col.insert_one({"name": request.form.get('n'), "price": request.form.get('p'), "img": res['secure_url'], "date_added": datetime.now()})
    except: pass
    return redirect(url_for('admin'))

@app.route('/submit-review', methods=['POST'])
def submit_review():
    reviews_col.insert_one({"name": request.form.get('rev_name'), "msg": request.form.get('rev_msg'), "date": datetime.now()})
    return redirect("/")

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
