import os
import certifi
from flask import Flask, request, redirect, render_template_string, url_for, session
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "verma_pustak_secret_key_2071")

# --- MONGODB CONFIGURATION ---
ca = certifi.where()
client = MongoClient(
    os.environ.get("MONGO_URI"),
    tlsCAFile=ca,
    tlsAllowInvalidCertificates=True,
    connect=False
)
db = client['verma_pustak_db']
inventory_col = db['inventory']
reviews_col = db['reviews']
leads_col = db['leads']
settings_col = db['settings']

# --- CLOUDINARY CONFIGURATION ---
cloudinary.config(
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key = os.environ.get("CLOUDINARY_API_KEY"),
    api_secret = os.environ.get("CLOUDINARY_API_SECRET")
)

ADMIN_PASSWORD = "verma@123"
CATEGORIES = ["Textbooks", "Stationery", "Calculators", "Other"]

# --- LOAD SETTINGS FROM DB OR USE DEFAULT ---
def get_settings():
    default = {
        "shop_name": "Verma Pustak Pasal",
        "phone": "9779847299546",
        "fb_url": "https://www.facebook.com/verma.pustak.pasal",
        "announcement": "📢 NEW SESSION SALE: GET UP TO 10% OFF!",
        "map_html": '<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3545.1!2d83.6!3d27.5" width="100%" height="380" style="border:0;" allowfullscreen=""></iframe>',
        "logo_url": "https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg",
        "group_link": "https://chat.whatsapp.com/CAj5KOwL2EuAlmPQmOH5rX"
    }
    s = settings_col.find_one({"type": "general"})
    return s if s else default

# --- UNIFIED CSS ---
SITE_CSS = '''
<style>
    :root { --primary: #2c3e50; --secondary: #25d366; --accent: #4f46e5; --bg: #f8fafd; --card-bg: white; --text: #333; }
    [data-theme="dark"] { --bg: #121212; --card-bg: #1e1e1e; --text: #ffffff; }
    body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', sans-serif; margin: 0; padding-bottom: 20px; }
    .announcement-bar { background: var(--secondary); color: white; padding: 10px; text-align: center; font-weight: bold; }
    .header { background: var(--primary); color: white; padding: 40px 0 100px 0; text-align: center; }
    .logo-box { background: white; display: inline-block; padding: 5px; border-radius: 10px; width: 120px; }
    .logo-img { width: 100%; height: auto; border-radius: 5px; }
    .section-card { background: var(--card-bg); border-radius: 15px; padding: 25px; margin: -60px auto 40px auto; max-width: 900px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
    .product-card { background: var(--card-bg); border-radius: 12px; padding: 15px; text-align: center; border: 1px solid rgba(0,0,0,0.05); height: 100%; }
    .theme-toggle { position: fixed; top: 15px; right: 15px; z-index: 3000; border: none; border-radius: 50%; width: 40px; height: 40px; cursor: pointer; }
    footer { background: var(--primary); color: white; padding: 30px 0; text-align: center; margin-top: 50px; }
</style>
'''

@app.route('/')
def home():
    settings = get_settings()
    hour = datetime.now().hour
    greeting = "Good Morning! ☀️" if hour < 12 else "Good Afternoon! 🌤️" if hour < 17 else "Good Evening! 🌙"
    selected_cat = request.args.get('category', 'All')
    
    query = {} if selected_cat == "All" else {"cat": selected_cat}
    inventory = list(inventory_col.find(query).sort("date_added", -1))
    reviews = list(reviews_col.find().sort("date", -1))

    cat_btns = f'<a href="/" class="btn btn-sm btn-outline-primary m-1 {"active" if selected_cat == "All" else ""}">All</a>'
    for c in CATEGORIES:
        cat_btns += f'<a href="/?category={c}" class="btn btn-sm btn-outline-primary m-1 {"active" if selected_cat == c else ""}">{c}</a>'

    items_html = ""
    for p in inventory:
        items_html += f'''
        <div class="col-md-4 mb-4">
            <div class="product-card shadow-sm">
                <img src="{p['img']}" style="width:100%; height:180px; object-fit:contain;">
                <h5 class="fw-bold mt-2">{p['name']}</h5>
                <p class="fw-bold text-success">Rs. {p['price']}</p>
                <a href="https://wa.me/{settings['phone']}?text=Order: {p['name']}" class="btn btn-success btn-sm w-100">Order on WhatsApp</a>
            </div>
        </div>'''

    rev_html = "".join([f'<div class="mb-2 p-2 border-bottom small"><strong>{r["name"]}</strong> ({"★"*int(r["rating"])})<br>{r["msg"]}</div>' for r in reviews])

    return render_template_string(f'''
    <!DOCTYPE html>
    <html lang="en" data-theme="light">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{settings['shop_name']}</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">{SITE_CSS}</head>
    <body>
        <button class="theme-toggle" onclick="toggleTheme()">🌓</button>
        <div class="announcement-bar">{settings['announcement']}</div>
        <header class="header">
            <div class="logo-box"><img src="{settings['logo_url']}" class="logo-img"></div>
            <h1>{settings['shop_name']}</h1>
            <p>Ramgram-3, Parasi | 📞 {settings['phone']}</p>
        </header>

        <div class="container mt-2">
            <div class="section-card text-center">
                <h3>{greeting}</h3>
                <form action="/subscribe" method="POST" class="row g-2 justify-content-center mt-3">
                    <div class="col-md-4"><input name="n" class="form-control" placeholder="Name" required></div>
                    <div class="col-md-4"><input name="p" class="form-control" placeholder="WhatsApp No" required></div>
                    <div class="col-md-2"><button type="submit" class="btn btn-dark w-100">JOIN</button></div>
                </form>
            </div>
            <div class="text-center mb-4">{cat_btns}</div>
            <div class="row">{items_html if items_html else "<p class='text-center'>No items in stock.</p>"}</div>
            
            <div class="row mt-5">
                <div class="col-md-6 mb-4"><h4>Location 📍</h4>{settings['map_html']}</div>
                <div class="col-md-6">
                    <h4>Reviews</h4>
                    <div style="max-height:200px; overflow-y:auto;" class="mb-3">{rev_html if rev_html else "No reviews."}</div>
                    <form action="/submit-review" method="POST" class="p-3 border rounded">
                        <input name="rev_name" class="form-control mb-2" placeholder="Your Name" required>
                        <select name="rev_rating" class="form-control mb-2"><option value="5">5 Star</option><option value="4">4 Star</option></select>
                        <textarea name="rev_msg" class="form-control mb-2" placeholder="Message" required></textarea>
                        <button class="btn btn-dark w-100 btn-sm">Submit</button>
                    </form>
                </div>
            </div>
        </div>
        <footer><p>© 2026 {settings['shop_name']} | <a href="/admin" class="text-white">Admin</a></p></footer>
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

# --- ADMIN PANEL ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        if request.method == 'POST' and request.form.get('password') == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        return '<div style="text-align:center; padding-top:100px;"><form method="POST"><h2>Admin</h2><input type="password" name="password"><button>Login</button></form></div>'

    settings = get_settings()
    inventory = list(inventory_col.find())
    leads = list(leads_col.find())
    
    prod_rows = "".join([f"<tr><td>{p['name']}</td><td>Rs.{p['price']}</td><td><a href='/delete-product/{p['_id']}' class='text-danger'>Delete</a></td></tr>" for p in inventory])
    lead_rows = "".join([f"<tr><td>{l['name']}</td><td>{l['phone']}</td><td>{l['class']}</td></tr>" for l in leads])

    return render_template_string(f'''
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <div class="container py-4">
        <div class="d-flex justify-content-between mb-4"><h2>Management Dashboard</h2><a href="/logout" class="btn btn-danger">Logout</a></div>
        <div class="row">
            <div class="col-md-4">
                <div class="card p-3 shadow-sm mb-3">
                    <h5>Add Product</h5>
                    <form action="/add-product" method="POST" enctype="multipart/form-data">
                        <input name="n" placeholder="Name" class="form-control mb-2" required>
                        <input name="p" placeholder="Price" class="form-control mb-2" required>
                        <select name="cat" class="form-select mb-2">{"".join([f"<option>{c}</option>" for c in CATEGORIES])}</select>
                        <input type="file" name="file" class="form-control mb-2" required>
                        <button class="btn btn-primary w-100">Add Product</button>
                    </form>
                </div>
            </div>
            <div class="col-md-8">
                <div class="card p-3 shadow-sm mb-3">
                    <h5>Shop Settings</h5>
                    <form action="/update-settings" method="POST" enctype="multipart/form-data">
                        <input name="shop_name" value="{settings['shop_name']}" class="form-control mb-2">
                        <input name="phone" value="{settings['phone']}" class="form-control mb-2">
                        <input name="group_link" value="{settings['group_link']}" class="form-control mb-2">
                        <textarea name="announcement" class="form-control mb-2">{settings['announcement']}</textarea>
                        <input type="file" name="logo" class="form-control mb-2">
                        <button class="btn btn-success w-100">Save Settings</button>
                    </form>
                </div>
                <div class="card p-3 shadow-sm">
                    <h5>Student Leads</h5>
                    <table class="table table-sm"><thead><tr><th>Name</th><th>Phone</th><th>Class</th></tr></thead><tbody>{lead_rows}</tbody></table>
                </div>
            </div>
        </div>
        <div class="card p-3 mt-3 shadow-sm">
            <h5>Current Inventory</h5>
            <table class="table"><tbody>{prod_rows}</tbody></table>
        </div>
    </div>
    ''')

# --- HELPERS ---
@app.route('/update-settings', methods=['POST'])
def update_settings():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    data = {
        "shop_name": request.form.get('shop_name'),
        "phone": request.form.get('phone'),
        "group_link": request.form.get('group_link'),
        "announcement": request.form.get('announcement'),
        "type": "general"
    }
    if 'logo' in request.files and request.files['logo'].filename != '':
        res = cloudinary.uploader.upload(request.files['logo'])
        data["logo_url"] = res['secure_url']
    
    settings_col.update_one({"type": "general"}, {"$set": data}, upsert=True)
    return redirect(url_for('admin'))

@app.route('/add-product', methods=['POST'])
def add_product():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    res = cloudinary.uploader.upload(request.files['file'])
    inventory_col.insert_one({
        "name": request.form.get('n'),
        "price": request.form.get('p'),
        "cat": request.form.get('cat'),
        "img": res['secure_url'],
        "date_added": datetime.now()
    })
    return redirect(url_for('admin'))

@app.route('/delete-product/<id>')
def delete_product(id):
    if not session.get('logged_in'): return redirect(url_for('admin'))
    inventory_col.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('admin'))

@app.route('/submit-review', methods=['POST'])
def submit_review():
    reviews_col.insert_one({
        "name": request.form.get('rev_name'),
        "rating": request.form.get('rev_rating'),
        "msg": request.form.get('rev_msg'),
        "date": datetime.now()
    })
    return redirect(url_for('home'))

@app.route('/subscribe', methods=['POST'])
def subscribe():
    leads_col.insert_one({
        "name": request.form.get('n'),
        "phone": request.form.get('p'),
        "class": request.form.get('c'),
        "date": datetime.now()
    })
    settings = get_settings()
    return redirect(settings['group_link'])

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
