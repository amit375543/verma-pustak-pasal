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
inventory_col = db['inventory']
reviews_col = db['reviews']
leads_col = db['leads']
settings_col = db['settings']

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
        "fb_url": "https://facebook.com/vermapustakpasal",
        "announcement": "📢 Welcome to Verma Pustak Pasal! Quality you can trust.",
        "map_html": '<iframe src="https://www.google.com/maps/embed?pb=..." width="100%" height="300" style="border:0;" allowfullscreen=""></iframe>',
        "logo_url": "https://via.placeholder.com/150",
        "group_link": "https://chat.whatsapp.com/..."
    }
    s = settings_col.find_one({"type": "general"})
    if s: s.pop('_id', None)
    return s if s else default

# --- ALL-IN-ONE CSS ---
SITE_CSS = '''
<style>
    :root { --primary: #2c3e50; --secondary: #25d366; --bg: #f8fafd; --card: #fff; --text: #333; --greet: #ff5722; }
    [data-theme="dark"] { --primary: #1a1a1a; --bg: #121212; --card: #1e1e1e; --text: #fff; --greet: #ffeb3b; }
    body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', sans-serif; transition: 0.3s; margin: 0; }
    .announcement { background: var(--secondary); color: white; padding: 12px; text-align: center; font-weight: bold; }
    .header { background: var(--primary); color: white; padding: 40px 0 100px 0; text-align: center; }
    .logo-box { background: white; display: inline-block; padding: 8px; border-radius: 12px; width: 130px; margin-bottom: 10px; }
    .section-card { background: var(--card); border-radius: 15px; padding: 30px; margin: -70px auto 40px auto; max-width: 900px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); position: relative; z-index: 10; }
    .prod-card { background: var(--card); border-radius: 12px; padding: 15px; text-align: center; border: 1px solid rgba(0,0,0,0.05); transition: 0.3s; height: 100%; }
    .prod-card:hover { transform: translateY(-5px); }
    .theme-toggle { position: fixed; top: 15px; right: 15px; z-index: 2000; cursor: pointer; border: none; background: white; border-radius: 50%; width: 40px; height: 40px; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }
    .wa-float { position: fixed; bottom: 20px; right: 20px; background: #25d366; color: white; padding: 15px; border-radius: 50px; text-decoration: none; font-weight: bold; box-shadow: 0 4px 15px rgba(0,0,0,0.3); z-index: 1000; }
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
    reviews = list(reviews_col.find().sort("date", -1).limit(6))

    items_html = "".join([f'''
        <div class="col-md-4 mb-4">
            <div class="prod-card shadow-sm">
                <img src="{p['img']}" style="width:100%; height:180px; object-fit:contain;">
                <h5 class="mt-3 fw-bold">{p['name']}</h5>
                <p class="text-success fw-bold">Rs. {p['price']}</p>
                <a href="https://wa.me/{settings['phone']}?text=I want to order {p['name']}" class="btn btn-success btn-sm w-100">Order Now</a>
            </div>
        </div>''' for p in inventory])

    rev_html = "".join([f'<div class="mb-3 p-2 border-bottom"><strong>{r["name"]}</strong> ({"★"*int(r["rating"])})<p class="small mb-0">{r["msg"]}</p></div>' for r in reviews])

    return render_template_string(f'''
    <!DOCTYPE html>
    <html lang="en" data-theme="light">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{settings['shop_name']}</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">{SITE_CSS}</head>
    <body>
        <button class="theme-toggle" onclick="toggleTheme()">🌓</button>
        <div class="announcement">{settings['announcement']}</div>
        <header class="header">
            <div class="logo-box"><img src="{settings['logo_url']}" style="width:100%;"></div>
            <h1>{settings['shop_name']}</h1>
            <p>Ramgram-3, Parasi | 📞 {settings['phone']}</p>
        </header>

        <a href="https://wa.me/{settings['phone']}" class="wa-float">Chat on WhatsApp</a>

        <div class="container">
            <div class="section-card text-center">
                <h2 style="color:var(--greet);">{greeting}</h2>
                <form action="/subscribe" method="POST" class="row g-2 mt-3 justify-content-center">
                    <div class="col-md-4"><input name="n" class="form-control" placeholder="Student Name" required></div>
                    <div class="col-md-3"><input name="p" class="form-control" placeholder="WhatsApp No" required></div>
                    <div class="col-md-2"><input name="c" class="form-control" placeholder="Class" required></div>
                    <div class="col-md-2"><button class="btn btn-dark w-100">JOIN GROUP</button></div>
                </form>
            </div>

            <div class="text-center mb-4">
                <a href="/" class="btn btn-sm btn-outline-primary m-1">All</a>
                {"".join([f'<a href="/?category={c}" class="btn btn-sm btn-outline-primary m-1">{c}</a>' for c in CATEGORIES])}
            </div>

            <div class="row">{items_html if items_html else "<p class='text-center'>No products yet.</p>"}</div>

            <div class="row mt-5">
                <div class="col-md-6 mb-4"><h4>Find Us 📍</h4><div class="border rounded overflow-hidden">{settings['map_html']}</div></div>
                <div class="col-md-6">
                    <h4>Student Reviews</h4>
                    <div style="max-height:250px; overflow-y:auto;" class="mb-3">{rev_html if rev_html else "No reviews yet."}</div>
                    <form action="/submit-review" method="POST" class="p-3 border rounded bg-white">
                        <input name="rev_name" class="form-control mb-2" placeholder="Your Name" required>
                        <select name="rev_rating" class="form-control mb-2"><option value="5">★★★★★ (5 Star)</option><option value="4">★★★★ (4 Star)</option></select>
                        <textarea name="rev_msg" class="form-control mb-2" placeholder="Your Review" required></textarea>
                        <button class="btn btn-dark btn-sm w-100">Post Review</button>
                    </form>
                </div>
            </div>
        </div>

        <footer class="mt-5 p-4 bg-dark text-white text-center">
            <p>© 2026 {settings['shop_name']} | <a href="/admin" class="text-white">Admin Dashboard</a></p>
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

# --- ADMIN DASHBOARD ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        if request.method == 'POST' and request.form.get('password') == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        return '<div style="text-align:center; margin-top:100px;"><form method="POST"><h2>Admin Access</h2><input type="password" name="password"><button>Login</button></form></div>'

    settings = get_settings()
    inventory = list(inventory_col.find())
    leads = list(leads_col.find().sort("date", -1))
    
    prod_rows = "".join([f"<tr><td><img src='{p['img']}' width='40'></td><td>{p['name']}</td><td>Rs.{p['price']}</td><td><a href='/delete-product/{p['_id']}' class='btn btn-sm btn-danger'>X</a></td></tr>" for p in inventory])
    lead_rows = "".join([f"<tr><td>{l['name']}</td><td>{l['phone']}</td><td>{l['class']}</td></tr>" for l in leads])

    return render_template_string(f'''
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <div class="container py-5">
        <div class="d-flex justify-content-between mb-4"><h2>Management Dashboard ⚙️</h2><a href="/logout" class="btn btn-outline-danger">Logout</a></div>
        <div class="row">
            <div class="col-md-5">
                <div class="card p-3 shadow-sm mb-4">
                    <h5>Shop Branding</h5>
                    <form action="/update-settings" method="POST" enctype="multipart/form-data">
                        <label class="small">Shop Name</label><input name="shop_name" value="{settings['shop_name']}" class="form-control mb-2">
                        <label class="small">WhatsApp</label><input name="phone" value="{settings['phone']}" class="form-control mb-2">
                        <label class="small">Announcement</label><textarea name="announcement" class="form-control mb-2">{settings['announcement']}</textarea>
                        <label class="small">Map HTML Embed Code</label><textarea name="map_html" class="form-control mb-2">{settings['map_html']}</textarea>
                        <label class="small">Update Logo</label><input type="file" name="logo" class="form-control mb-3">
                        <button class="btn btn-success w-100">Save Changes</button>
                    </form>
                </div>
            </div>
            <div class="col-md-7">
                <div class="card p-3 shadow-sm mb-4">
                    <h5>Add Book to Stock</h5>
                    <form action="/add-product" method="POST" enctype="multipart/form-data" class="row g-2">
                        <div class="col-8"><input name="n" placeholder="Name" class="form-control" required></div>
                        <div class="col-4"><input name="p" placeholder="Price" class="form-control" required></div>
                        <div class="col-8"><select name="cat" class="form-select">{"".join([f"<option>{c}</option>" for c in CATEGORIES])}</select></div>
                        <div class="col-4"><input type="file" name="file" class="form-control" required></div>
                        <div class="col-12"><button class="btn btn-primary w-100">Add Product</button></div>
                    </form>
                </div>
                <div class="card p-3 shadow-sm">
                    <h5>Inventory List</h5>
                    <table class="table table-sm"><tbody>{prod_rows}</tbody></table>
                </div>
            </div>
        </div>
        <div class="card p-3 mt-4 shadow-sm">
            <h5>Student Leads (WhatsApp Group Requests)</h5>
            <table class="table table-hover"><thead><tr><th>Name</th><th>Phone</th><th>Class</th></tr></thead><tbody>{lead_rows}</tbody></table>
        </div>
    </div>
    ''')

# --- ACTIONS ---
@app.route('/update-settings', methods=['POST'])
def update_settings():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    data = {
        "shop_name": request.form.get('shop_name'),
        "phone": request.form.get('phone'),
        "announcement": request.form.get('announcement'),
        "map_html": request.form.get('map_html'),
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
    s = get_settings()
    return redirect(s['group_link'])

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
