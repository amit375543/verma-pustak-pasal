import os
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "verma_pustak_secret_key_2071")

# --- MONGODB CONFIGURATION ---
mongo_uri = os.environ.get("MONGO_URI")
client = MongoClient(mongo_uri)
db = client['verma_pustak_db']

# Collections
settings_col = db['settings']
inventory_col = db['inventory']
reviews_col = db['reviews']
leads_col = db['leads']

# Initialize Default Settings if Database is Empty
def get_settings():
    default_settings = {
        "shop_name": "Verma Pustak Pasal",
        "phone": "9779847299546",
        "fb_url": "https://www.facebook.com/verma.pustak.pasal",
        "announcement": "📢 NEW SESSION SALE: GET UP TO 10% OFF!",
        "map_html": '<iframe src="https://www.google.com/maps/embed?pb=..." width="100%" height="380" style="border:0;" allowfullscreen="" loading="lazy"></iframe>',
        "logo_url": "https://i.ibb.co/vzPRm8f/logo.png", # Use a stable URL
        "group_link": "https://chat.whatsapp.com/..."
    }
    existing = settings_col.find_one({"type": "config"})
    return existing if existing else default_settings

ADMIN_PASSWORD = "verma@123"
CATEGORIES = ["Textbooks", "Stationery", "Calculators", "Other"]

# --- UNIFIED CSS ---
SITE_CSS = '''
<style>
    :root { --primary: #2c3e50; --secondary: #25d366; --accent: #4f46e5; --bg: #f8fafd; --card-bg: white; --text: #333; --greeting-color: #ff5722; }
    [data-theme="dark"] { --primary: #1a1a1a; --secondary: #1db954; --bg: #121212; --card-bg: #1e1e1e; --text: #ffffff; --greeting-color: #ffeb3b; }
    body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', sans-serif; margin: 0; padding-bottom: 20px; transition: 0.3s; }
    .announcement-bar { background: var(--secondary); color: white; padding: 12px; text-align: center; font-weight: 800; }
    .header { background: var(--primary); color: white; padding: 40px 0 120px 0; text-align: center; border-bottom: 5px solid var(--secondary); }
    .logo-box { background: white; display: inline-block; padding: 8px; border-radius: 15px; margin-bottom: 12px; width: 140px; box-shadow: 0 5px 20px rgba(0,0,0,0.3); }
    .logo-img { width: 100%; border-radius: 10px; }
    .section-card { background: var(--card-bg); border-radius: 15px; padding: 35px; margin: -80px auto 40px auto; max-width: 1000px; box-shadow: 0 15px 35px rgba(0,0,0,0.15); position: relative; z-index: 10; }
    .product-card { background: var(--card-bg); border-radius: 15px; padding: 15px; text-align: center; border: 1px solid rgba(0,0,0,0.05); transition: 0.3s; }
    .product-card:hover { transform: translateY(-5px); }
    .theme-toggle { position: fixed; top: 15px; right: 15px; z-index: 3000; border-radius: 50%; width: 40px; height: 40px; border: none; cursor: pointer; }
    .floating-sidebar { position: fixed; bottom: 30px; right: 20px; display: flex; flex-direction: column; gap: 12px; z-index: 2000; }
    .side-icon { width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
</style>
'''

@app.route('/')
def home():
    settings = get_settings()
    hour = datetime.now().hour
    greeting = "Good Morning! ☀️" if hour < 12 else "Good Afternoon! 🌤️" if hour < 17 else "Good Evening! 🌙"
    
    selected_cat = request.args.get('category', 'All')
    query = {} if selected_cat == "All" else {"cat": selected_cat}
    
    products = list(inventory_col.find(query))
    reviews = list(reviews_col.find().sort("_id", -1).limit(10))

    cat_btns = f'<a href="/" class="btn btn-sm btn-outline-primary m-1 {"active" if selected_cat == "All" else ""}">All</a>'
    for c in CATEGORIES:
        cat_btns += f'<a href="/?category={c}" class="btn btn-sm btn-outline-primary m-1 {"active" if selected_cat == c else ""}">{c}</a>'

    items_html = ""
    for p in products:
        items_html += f'''
        <div class="col-md-4 mb-4">
            <div class="product-card shadow-sm">
                <span class="badge bg-secondary mb-2">{p['cat']}</span>
                <img src="{p['img']}" style="width:100%; height:150px; object-fit:contain;">
                <h5 class="fw-bold mt-2">{p['name']}</h5>
                <p class="fw-bold fs-5 text-primary">Rs. {p['price']}</p>
                <a href="https://wa.me/{settings['phone']}?text=I want to buy: {p['name']}" class="btn btn-success w-100 fw-bold">Order on WhatsApp</a>
            </div>
        </div>'''

    return render_template_string(f'''
    <!DOCTYPE html>
    <html lang="en" data-theme="light">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{settings['shop_name']}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">{SITE_CSS}</head>
    <body>
        <button class="theme-toggle" onclick="toggleTheme()">🌓</button>
        <div class="announcement-bar">{settings['announcement']}</div>
        <header class="header">
            <div class="logo-box"><img src="{settings['logo_url']}" class="logo-img"></div>
            <h1 class="fw-bold m-0">{settings['shop_name']}</h1>
            <p class="fs-6 opacity-75">📞 {settings['phone']}</p>
        </header>

        <div class="floating-sidebar">
            <a href="{settings['group_link']}" target="_blank" class="side-icon bg-success"><img src="https://cdn-icons-png.flaticon.com/512/733/733585.png" width="25"></a>
        </div>

        <div class="container">
            <div class="section-card text-center shadow-lg">
                <h2 class="greeting-text mb-1">{greeting}</h2>
                <form action="/subscribe" method="POST" class="row g-2 justify-content-center mt-3">
                    <div class="col-md-4"><input name="n" class="form-control" placeholder="Your Name" required></div>
                    <div class="col-md-4"><input name="p" class="form-control" placeholder="WhatsApp Number" required></div>
                    <div class="col-md-2"><button type="submit" class="btn btn-dark w-100">JOIN</button></div>
                </form>
            </div>
            <div class="text-center mb-4">{cat_btns}</div>
            <div class="row">{items_html}</div>
            
            <div class="row mt-5">
                <div class="col-md-6 mb-4">{settings['map_html']}</div>
                <div class="col-md-6">
                    <h4>Reviews</h4>
                    <form action="/submit-review" method="POST" class="mb-3">
                        <input name="rev_name" class="form-control mb-2" placeholder="Name" required>
                        <textarea name="rev_msg" class="form-control mb-2" placeholder="Your experience..." required></textarea>
                        <button class="btn btn-primary btn-sm">Submit</button>
                    </form>
                    <div style="max-height:300px; overflow-y:auto;">
                        {"".join([f"<div class='border-bottom mb-2'><strong>{r['name']}</strong>: {r['review']}</div>" for r in reviews])}
                    </div>
                </div>
            </div>
        </div>
        <footer class="text-center mt-5 p-4 bg-dark text-white"><p>© 2026 {settings['shop_name']} | <a href="/admin" class="text-white">Admin</a></p></footer>
        <script>function toggleTheme() {{ const b = document.documentElement; const t = b.getAttribute('data-theme') === 'light' ? 'dark' : 'light'; b.setAttribute('data-theme', t); localStorage.setItem('theme', t); }} document.documentElement.setAttribute('data-theme', localStorage.getItem('theme') || 'light');</script>
    </body></html>
    ''')

# --- ADMIN PANEL ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        if request.method == 'POST' and request.form.get('password') == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        return '<body style="background:#2c3e50; text-align:center; padding-top:100px;"><form method="POST" style="background:white; display:inline-block; padding:30px; border-radius:10px;"><h3>Admin Login</h3><input type="password" name="password" class="form-control mb-3"><button class="btn btn-primary">Login</button></form></body>'

    settings = get_settings()
    leads = list(leads_col.find())
    products = list(inventory_col.find())
    
    return render_template_string(f'''
    <!DOCTYPE html>
    <html><head><title>Admin</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
    <body class="bg-light p-4">
        <div class="container">
            <div class="d-flex justify-content-between mb-4"><h2>Shop Manager ⚙️</h2><a href="/logout" class="btn btn-danger">Logout</a></div>
            <div class="row">
                <div class="col-md-5">
                    <div class="card p-3 mb-4">
                        <h5>Settings</h5>
                        <form action="/update-settings" method="POST">
                            <input name="shop_name" value="{settings['shop_name']}" class="form-control mb-2">
                            <input name="phone" value="{settings['phone']}" class="form-control mb-2">
                            <input name="logo_url" value="{settings['logo_url']}" class="form-control mb-2" placeholder="Logo URL">
                            <textarea name="announcement" class="form-control mb-2">{settings['announcement']}</textarea>
                            <button class="btn btn-success w-100">Update Branding</button>
                        </form>
                    </div>
                    <div class="card p-3">
                        <h5>Add Book</h5>
                        <form action="/add-product" method="POST">
                            <input name="n" placeholder="Book Name" class="form-control mb-2" required>
                            <input name="p" placeholder="Price" class="form-control mb-2" required>
                            <select name="cat" class="form-select mb-2">{"".join([f'<option>{c}</option>' for c in CATEGORIES])}</select>
                            <input name="img" placeholder="Image URL (ImgBB)" class="form-control mb-2" required>
                            <button class="btn btn-primary w-100">Add to Shop</button>
                        </form>
                    </div>
                </div>
                <div class="col-md-7">
                    <h5>Inventory</h5>
                    <table class="table bg-white">
                        {"".join([f"<tr><td>{p['name']}</td><td>Rs.{p['price']}</td><td><a href='/delete-product/{p['_id']}'>❌</a></td></tr>" for p in products])}
                    </table>
                    <h5 class="mt-4">Student Leads</h5>
                    <table class="table bg-white">
                        {"".join([f"<tr><td>{l['name']}</td><td>{l['phone']}</td></tr>" for l in leads])}
                    </table>
                </div>
            </div>
        </div>
    </body></html>
    ''')

# --- HELPERS ---
@app.route('/update-settings', methods=['POST'])
def update_settings():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    new_data = {
        "type": "config",
        "shop_name": request.form.get('shop_name'),
        "phone": request.form.get('phone'),
        "logo_url": request.form.get('logo_url'),
        "announcement": request.form.get('announcement'),
        "fb_url": get_settings()['fb_url'],
        "map_html": get_settings()['map_html'],
        "group_link": get_settings()['group_link']
    }
    settings_col.update_one({"type": "config"}, {"$set": new_data}, upsert=True)
    return redirect(url_for('admin'))

@app.route('/add-product', methods=['POST'])
def add_product():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    inventory_col.insert_one({
        "name": request.form.get('n'),
        "price": request.form.get('p'),
        "cat": request.form.get('cat'),
        "img": request.form.get('img'),
        "date": datetime.now()
    })
    return redirect(url_for('admin'))

@app.route('/delete-product/<id>')
def delete_product(id):
    if not session.get('logged_in'): return redirect(url_for('admin'))
    inventory_col.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('admin'))

@app.route('/submit-review', methods=['POST'])
def submit_review():
    reviews_col.insert_one({"name": request.form.get('rev_name'), "review": request.form.get('rev_msg')})
    return redirect(url_for('home'))

@app.route('/subscribe', methods=['POST'])
def subscribe():
    leads_col.insert_one({"name": request.form.get('n'), "phone": request.form.get('p'), "date": datetime.now()})
    return redirect(get_settings()['group_link'])

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run()
