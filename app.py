import os
import certifi
from flask import Flask, request, redirect, render_template_string, url_for, session
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "verma_pustak_2071_fixed")

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
        "shop_name": "Verma Pustak Pasal",
        "phone": "9847299546",
        "announcement": "Welcome to Verma Pustak Pasal!",
        "logo_url": "https://via.placeholder.com/150",
        "group_link": "#"
    }
    try:
        s = settings_col.find_one({"type": "general"})
        if s:
            # We build the dictionary safely to avoid KeyError
            return {
                "shop_name": s.get("shop_name", default["shop_name"]),
                "phone": s.get("phone", default["phone"]),
                "announcement": s.get("announcement", default["announcement"]),
                "logo_url": s.get("logo_url", default["logo_url"]),
                "group_link": s.get("group_link", default["group_link"])
            }
    except:
        pass
    return default

# --- UI STYLES ---
SITE_CSS = '''
<style>
    :root { --p: #2c3e50; --s: #25d366; --bg: #f8fafd; --card: #fff; --text: #333; }
    body { background: var(--bg); color: var(--text); font-family: sans-serif; margin: 0; }
    .announcement { background: var(--s); color: white; padding: 10px; text-align: center; font-weight: bold; }
    .header { background: var(--p); color: white; padding: 30px; text-align: center; }
    .section-card { background: var(--card); border-radius: 12px; padding: 20px; margin: 20px auto; max-width: 800px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
    .prod-card { background: var(--card); border-radius: 10px; padding: 15px; text-align: center; border: 1px solid rgba(0,0,0,0.05); margin-bottom: 20px; }
</style>
'''

@app.route('/')
def home():
    settings = get_settings()
    try:
        inventory = list(inventory_col.find().sort("date_added", -1))
    except:
        inventory = []
    
    items_html = ""
    for p in inventory:
        # Use .get() to avoid crashing if a key is missing
        img = p.get('img', 'https://via.placeholder.com/150')
        name = p.get('name', 'Unnamed Book')
        price = p.get('price', '0')
        items_html += f'''
        <div style="width: 30%; display: inline-block; vertical-align: top; padding: 10px;">
            <div class="prod-card">
                <img src="{img}" style="height:150px; object-fit:contain; width:100%;">
                <h5 class="mt-2">{name}</h5>
                <p class="text-success fw-bold">Rs. {price}</p>
                <a href="https://wa.me/{settings['phone']}" style="background:#25d366; color:white; padding:5px 10px; text-decoration:none; border-radius:5px;">Order</a>
            </div>
        </div>'''

    return render_template_string(f'''
    <!DOCTYPE html>
    <html lang="en">
    <head><meta name="viewport" content="width=device-width, initial-scale=1">{SITE_CSS}</head>
    <body>
        <div class="announcement">{settings['announcement']}</div>
        <header class="header">
            <img src="{settings['logo_url']}" style="width:80px; border-radius:50%; background:white; padding:5px;">
            <h1>{settings['shop_name']}</h1>
            <p>Parasi, Nepal | {settings['phone']}</p>
        </header>
        <div style="padding: 20px; text-align: center;">
            <div class="section-card">
                <form action="/subscribe" method="POST">
                    <input name="p" placeholder="WhatsApp Number" required style="padding:10px; width:60%;">
                    <button type="submit" style="padding:10px; background:#2c3e50; color:white;">JOIN GROUP</button>
                </form>
            </div>
            <div style="max-width: 1000px; margin: auto;">{items_html if items_html else "<p>No books added yet. Go to /admin to add some!</p>"}</div>
        </div>
        <footer style="text-align:center; padding:20px; background:#2c3e50; color:white; margin-top:50px;">
            <p>© 2026 {settings['shop_name']} | <a href="/admin" style="color:white;">Admin Login</a></p>
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
        return '<div style="text-align:center; margin-top:100px;"><form method="POST"><h2>Admin</h2><input type="password" name="password" style="padding:10px;"><button style="padding:10px;">Login</button></form></div>'
    
    settings = get_settings()
    return render_template_string(f'''
    <div style="max-width:800px; margin:auto; padding:20px; font-family:sans-serif;">
        <h2>Admin Dashboard</h2><a href="/logout">Logout</a><hr>
        <div style="display:flex; gap:20px;">
            <div style="flex:1; border:1px solid #ddd; padding:15px;">
                <h3>Shop Settings</h3>
                <form action="/update-settings" method="POST">
                    Name: <br><input name="shop_name" value="{settings['shop_name']}" style="width:100%;"><br><br>
                    Phone: <br><input name="phone" value="{settings['phone']}" style="width:100%;"><br><br>
                    Notice: <br><textarea name="announcement" style="width:100%;">{settings['announcement']}</textarea><br><br>
                    Group Link: <br><input name="group_link" value="{settings['group_link']}" style="width:100%;"><br><br>
                    <button type="submit" style="background:green; color:white; padding:10px; width:100%;">Save Settings</button>
                </form>
            </div>
            <div style="flex:1; border:1px solid #ddd; padding:15px;">
                <h3>Add New Book</h3>
                <form action="/add-product" method="POST" enctype="multipart/form-data">
                    Book Name: <br><input name="n" required style="width:100%;"><br><br>
                    Price: <br><input name="p" required style="width:100%;"><br><br>
                    Image: <br><input type="file" name="file" required style="width:100%;"><br><br>
                    <button type="submit" style="background:blue; color:white; padding:10px; width:100%;">Upload Book</button>
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
        "announcement": request.form.get('announcement'),
        "group_link": request.form.get('group_link')
    }}, upsert=True)
    return redirect(url_for('admin'))

@app.route('/add-product', methods=['POST'])
def add_product():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    try:
        file = request.files['file']
        res = cloudinary.uploader.upload(file)
        inventory_col.insert_one({
            "name": request.form.get('n'),
            "price": request.form.get('p'),
            "img": res['secure_url'],
            "date_added": datetime.now()
        })
    except Exception as e:
        print(f"Error: {e}")
    return redirect(url_for('admin'))

@app.route('/subscribe', methods=['POST'])
def subscribe():
    leads_col.insert_one({"phone": request.form.get('p'), "date": datetime.now()})
    s = get_settings()
    return redirect(s['group_link'])

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
