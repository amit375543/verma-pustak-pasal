import os
import certifi
from flask import Flask, request, redirect, render_template_string, url_for, session
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "verma_pustak_2026_pro_stable")

# --- OPTIMIZED CONNECTION (Lazy Loading) ---
def get_db():
    ca = certifi.where()
    client = MongoClient(
        os.environ.get("MONGO_URI"),
        tlsCAFile=ca,
        tlsAllowInvalidCertificates=True,
        connect=False,  # Important: Prevents hanging at startup
        serverSelectionTimeoutMS=5000  # Give up fast if DB is slow
    )
    return client['verma_pustak_db']

# --- CLOUDINARY ---
cloudinary.config(
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key = os.environ.get("CLOUDINARY_API_KEY"),
    api_secret = os.environ.get("CLOUDINARY_API_SECRET")
)

ADMIN_PASSWORD = "verma@123"

def get_settings():
    db = get_db()
    default = {
        "shop_name": "Verma Pustak Pasal",
        "phone": "9847299546",
        "announcement": "📢 Quality you can trust!",
        "map_html": "Map loading...",
        "logo_url": "https://via.placeholder.com/150",
        "group_link": "#"
    }
    try:
        s = db.settings.find_one({"type": "general"})
        return s if s else default
    except:
        return default

# --- MINIMAL FAST UI ---
SITE_CSS = '''
<style>
    :root { --p: #2c3e50; --s: #25d366; --bg: #f8fafd; }
    body { background: var(--bg); font-family: sans-serif; margin: 0; color: #333; }
    .nav { background: var(--p); color: white; padding: 25px; text-align: center; }
    .announcement { background: var(--s); color: white; padding: 10px; text-align: center; font-weight: bold; }
    .card { background: white; border-radius: 8px; padding: 15px; margin: 15px auto; max-width: 800px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .btn { background: var(--p); color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; text-decoration: none; }
    .wa-btn { background: var(--s); color: white; padding: 8px 15px; border-radius: 5px; text-decoration: none; display: inline-block; }
</style>
'''

@app.route('/')
def home():
    db = get_db()
    settings = get_settings()
    try:
        inventory = list(db.inventory.find().sort("date_added", -1).limit(20))
    except:
        inventory = []

    items_html = "".join([f'''
        <div style="width: 30%; display: inline-block; vertical-align: top; padding: 10px; min-width: 250px;">
            <div class="card" style="text-align: center;">
                <img src="{p.get('img','')}" style="height:150px; object-fit:contain; width:100%;">
                <h4>{p.get('name','Book')}</h4>
                <p style="color:green; font-weight:bold;">Rs. {p.get('price','0')}</p>
                <a href="https://wa.me/{settings['phone']}" class="wa-btn">Order on WhatsApp</a>
            </div>
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
        <div style="padding: 20px; text-align: center;">
            <div class="card">
                <form action="/subscribe" method="POST">
                    <input name="p" placeholder="WhatsApp Number" required style="padding:10px; width:60%;">
                    <button class="btn">JOIN GROUP</button>
                </form>
            </div>
            {items_html if items_html else "<p>Welcome! Add products in /admin.</p>"}
            <div class="card" style="text-align:left;">
                <h4>Our Location</h4>
                {settings['map_html']}
            </div>
        </div>
        <footer style="text-align:center; padding:30px; background:#eee;">
            <a href="/admin">Admin Login</a>
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
        return '<div style="text-align:center; margin-top:100px;"><form method="POST"><h2>Admin</h2><input type="password" name="password"><button>Login</button></form></div>'
    
    settings = get_settings()
    return render_template_string(f'''
    <div style="max-width:800px; margin:auto; padding:20px; font-family:sans-serif;">
        <h2>Admin Dashboard</h2><a href="/logout">Logout</a><hr>
        <form action="/update-settings" method="POST" style="margin-bottom:30px;">
            <h3>Shop Settings</h3>
            Name: <input name="shop_name" value="{settings['shop_name']}" style="width:100%;"><br><br>
            Phone: <input name="phone" value="{settings['phone']}" style="width:100%;"><br><br>
            Notice: <textarea name="announcement" style="width:100%;">{settings['announcement']}</textarea><br><br>
            Map Embed: <textarea name="map_html" style="width:100%;">{settings['map_html']}</textarea><br><br>
            <button class="btn" style="background:green;">Update Shop</button>
        </form>
        <form action="/add-product" method="POST" enctype="multipart/form-data">
            <h3>Add Book</h3>
            Name: <input name="n" required style="width:100%;"><br><br>
            Price: <input name="p" required style="width:100%;"><br><br>
            Image: <input type="file" name="file" required style="width:100%;"><br><br>
            <button class="btn" style="background:blue;">Upload Book</button>
        </form>
    </div>
    ''')

@app.route('/update-settings', methods=['POST'])
def update_settings():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    db = get_db()
    db.settings.update_one({"type": "general"}, {"$set": {
        "shop_name": request.form.get('shop_name'),
        "phone": request.form.get('phone'),
        "announcement": request.form.get('announcement'),
        "map_html": request.form.get('map_html')
    }}, upsert=True)
    return redirect(url_for('admin'))

@app.route('/add-product', methods=['POST'])
def add_product():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    db = get_db()
    res = cloudinary.uploader.upload(request.files['file'])
    db.inventory.insert_one({
        "name": request.form.get('n'),
        "price": request.form.get('p'),
        "img": res['secure_url'],
        "date_added": datetime.now()
    })
    return redirect(url_for('admin'))

@app.route('/subscribe', methods=['POST'])
def subscribe():
    db = get_db()
    db.leads.insert_one({"phone": request.form.get('p'), "date": datetime.now()})
    return redirect("/")

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
