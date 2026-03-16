import certifi 
import os
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId
import cloudinary
import cloudinary.uploader
from pymongo import MongoClient
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "verma_pustak_2071_ultra")

# --- CLOUDINARY & MONGODB CONFIG ---
cloudinary.config(
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key = os.environ.get("CLOUDINARY_API_KEY"),
    api_secret = os.environ.get("CLOUDINARY_API_SECRET")
)

# --- DATABASE CONNECTION ---
mongo_uri = os.environ.get("MONGO_URI")

# Use certifi to find the correct system CA certificates for SSL
ca = certifi.where()

client = MongoClient(
    mongo_uri, 
    tlsCAFile=ca, # Use the certificate file
    tlsAllowInvalidCertificates=True, 
    connect=False, 
    serverSelectionTimeoutMS=5000
)

db = client['verma_pustak_db']

# Collections
settings_col = db['settings']
inventory_col = db['inventory']
reviews_col = db['reviews']
leads_col = db['leads']

# --- HELPERS ---
def get_settings():
    default = {
        "type": "config",
        "shop_name": "Verma Pustak Pasal",
        "phone": "9779847299546",
        "fb_url": "https://facebook.com/verma.pustak.pasal",
        "group_link": "https://chat.whatsapp.com/...",
        "announcement": "📢 NEW SESSION SALE IS LIVE!",
        "map_html": '<iframe src="https://www.google.com/maps/embed?..." width="100%" height="300" style="border:0;" allowfullscreen=""></iframe>',
        "logo_url": "https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg",
        "poster_url": ""  # If empty, popup is disabled
    }
    existing = settings_col.find_one({"type": "config"})
    return existing if existing else default

ADMIN_PASSWORD = "verma@123"
CATEGORIES = ["Textbooks", "Stationery", "Calculators", "Other"]

# --- UI COMPONENTS ---
SITE_CSS = '''
<style>
    :root { --primary: #2c3e50; --secondary: #25d366; --accent: #4f46e5; --bg: #f8fafd; --card-bg: white; --text: #333; --greeting-color: #ff5722; }
    [data-theme="dark"] { --primary: #1a1a1a; --secondary: #1db954; --bg: #121212; --card-bg: #1e1e1e; --text: #ffffff; --greeting-color: #ffeb3b; }
    body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', sans-serif; transition: 0.3s; margin:0; }
    .announcement-bar { background: var(--secondary); color: white; padding: 12px; text-align: center; font-weight: 800; }
    .header { background: var(--primary); color: white; padding: 40px 0 100px 0; text-align: center; border-bottom: 5px solid var(--secondary); }
    .logo-box { background: white; display: inline-block; padding: 10px; border-radius: 15px; width: 130px; margin-bottom: 10px; }
    .section-card { background: var(--card-bg); border-radius: 15px; padding: 30px; margin: -60px auto 40px auto; max-width: 900px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); position: relative; z-index: 10; }
    .product-card { background: var(--card-bg); border-radius: 15px; padding: 15px; text-align: center; height: 100%; border: 1px solid rgba(0,0,0,0.05); transition: 0.3s; }
    .product-card:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
    .floating-sidebar { position: fixed; bottom: 30px; right: 20px; display: flex; flex-direction: column; gap: 10px; z-index: 1000; }
    .side-icon { width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
    
    /* MODAL POPUP */
    #flashPoster { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 9999; display: flex; align-items: center; justify-content: center; }
    .poster-content { position: relative; max-width: 90%; max-height: 80%; }
    .poster-content img { width: 100%; border-radius: 15px; border: 4px solid white; }
    .close-poster { position: absolute; top: -15px; right: -15px; background: red; color: white; border: none; border-radius: 50%; width: 35px; height: 35px; cursor: pointer; font-weight: bold; }
</style>
'''

@app.route('/')
def home():
    s = get_settings()
    hour = datetime.now().hour
    greeting = "Good Morning! ☀️" if hour < 12 else "Good Afternoon! 🌤️" if hour < 17 else "Good Evening! 🌙"
    
    cat = request.args.get('category', 'All')
    products = list(inventory_col.find({} if cat == "All" else {"cat": cat}).sort("_id", -1))
    reviews = list(reviews_col.find().sort("_id", -1).limit(5))

    return render_template_string(f'''
    <!DOCTYPE html>
    <html lang="en" data-theme="light">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{{{{s.shop_name}}}}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">{SITE_CSS}</head>
    <body>
        {{% if s.poster_url %}}
        <div id="flashPoster"><div class="poster-content"><button class="close-poster" onclick="document.getElementById('flashPoster').style.display='none'">X</button><img src="{{{{s.poster_url}}}}"></div></div>
        {{% endif %}}

        <button class="btn btn-light shadow-sm" style="position:fixed; top:15px; right:15px; z-index:2000;" onclick="toggleTheme()">🌓</button>
        <div class="announcement-bar">{{{{s.announcement}}}}</div>
        
        <header class="header">
            <div class="logo-box"><img src="{{{{s.logo_url}}}}" style="width:100%; border-radius:10px;"></div>
            <h1 class="fw-bold m-0">{{{{s.shop_name}}}}</h1>
            <p class="opacity-75">📍 Ramgram-3, Parasi | 📞 {{{{s.phone}}}}</p>
        </header>

        <div class="floating-sidebar">
            <a href="{{{{s.group_link}}}}" target="_blank" class="side-icon bg-success"><img src="https://cdn-icons-png.flaticon.com/512/733/733585.png" width="24"></a>
            <a href="{{{{s.fb_url}}}}" target="_blank" class="side-icon bg-primary"><img src="https://cdn-icons-png.flaticon.com/512/733/733547.png" width="24"></a>
        </div>

        <div class="container">
            <div class="section-card text-center shadow">
                <h2 style="color:var(--greeting-color); font-weight:800;">{greeting}</h2>
                <form action="/subscribe" method="POST" class="row g-2 justify-content-center mt-3">
                    <div class="col-md-4"><input name="n" class="form-control" placeholder="Student Name" required></div>
                    <div class="col-md-4"><input name="p" class="form-control" placeholder="WhatsApp Number" required></div>
                    <div class="col-md-2"><button class="btn btn-dark w-100 fw-bold">REGISTER</button></div>
                </form>
            </div>

            <div class="text-center mb-4">
                <a href="/" class="btn btn-sm btn-outline-primary m-1">All</a>
                {" ".join([f'<a href="/?category={c}" class="btn btn-sm btn-outline-primary m-1">{c}</a>' for c in CATEGORIES])}
            </div>

            <div class="row">
                {{% for p in products %}}
                <div class="col-6 col-md-4 mb-4">
                    <div class="product-card shadow-sm">
                        <img src="{{{{p.img}}}}" style="width:100%; height:160px; object-fit:contain;">
                        <h6 class="fw-bold mt-2">{{{{p.name}}}}</h6>
                        <p class="fw-bold text-primary">Rs. {{{{p.price}}}}</p>
                        <a href="https://wa.me/{{{{s.phone}}}}?text=Order: {{{{p.name}}}}" class="btn btn-sm btn-success w-100">Order</a>
                    </div>
                </div>
                {{% endfor %}}
            </div>

            <div class="row mt-5">
                <div class="col-md-6 mb-4">{{{{s.map_html | safe}}}}</div>
                <div class="col-md-6">
                    <h4>Customer Feedback</h4>
                    <div class="bg-white p-3 border rounded mb-3" style="max-height:200px; overflow-y:auto;">
                        {{% for r in reviews %}}
                        <div class="border-bottom mb-2 small"><strong>{{{{r.name}}}}:</strong> {{{{r.review}}}}</div>
                        {{% endfor %}}
                    </div>
                    <form action="/submit-review" method="POST" class="p-3 border rounded bg-white shadow-sm">
                        <input name="rev_name" class="form-control form-control-sm mb-2" placeholder="Your Name" required>
                        <textarea name="rev_msg" class="form-control form-control-sm mb-2" placeholder="Write a review..." required></textarea>
                        <button class="btn btn-sm btn-dark w-100">Post Review</button>
                    </form>
                </div>
            </div>
        </div>
        <footer class="p-5 mt-5 bg-dark text-white text-center">
            <p>© 2026 {{{{s.shop_name}}}} | <a href="/admin" class="text-white">Admin Login</a></p>
        </footer>

        <script>
            function toggleTheme() {{
                const html = document.documentElement;
                const next = html.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
                html.setAttribute('data-theme', next);
                localStorage.setItem('theme', next);
            }}
            document.documentElement.setAttribute('data-theme', localStorage.getItem('theme') || 'light');
        </script>
    </body></html>
    ''', s=s, products=products, reviews=reviews)

# --- ADMIN PANEL ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        if request.method == 'POST' and request.form.get('password') == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        return '<body style="background:#2c3e50; text-align:center; padding-top:100px;"><form method="POST" style="background:white; padding:40px; border-radius:15px; display:inline-block;"><h3 class="mb-4">Admin Login</h3><input type="password" name="password" class="form-control mb-3"><button class="btn btn-primary w-100">Enter</button></form></body>'

    s = get_settings()
    prods = list(inventory_col.find())
    leads = list(leads_col.find())
    
    return render_template_string(f'''
    <!DOCTYPE html>
    <html><head><title>Admin Panel</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
    <body class="bg-light p-4">
        <div class="container">
            <div class="d-flex justify-content-between mb-4"><h2>Shop Management Center ⚙️</h2><a href="/logout" class="btn btn-danger">Logout</a></div>
            <div class="row">
                <div class="col-md-5">
                    <div class="card p-3 shadow-sm mb-4">
                        <h5>Shop Branding & Popup</h5>
                        <form action="/update-settings" method="POST" enctype="multipart/form-data">
                            <label class="small">Shop Name</label><input name="shop_name" value="{{{{s.shop_name}}}}" class="form-control mb-2">
                            <label class="small">Announcement</label><input name="announcement" value="{{{{s.announcement}}}}" class="form-control mb-2">
                            <label class="small">WhatsApp Link</label><input name="group_link" value="{{{{s.group_link}}}}" class="form-control mb-2">
                            <label class="small">Update Logo</label><input type="file" name="logo" class="form-control mb-2">
                            <label class="small text-primary fw-bold">Update Flash Poster (Popup)</label>
                            <input type="file" name="poster" class="form-control mb-2">
                            <a href="/clear-poster" class="btn btn-sm btn-outline-danger mb-3">Remove Popup Poster</a>
                            <button class="btn btn-success w-100">Save Changes</button>
                        </form>
                    </div>
                    <div class="card p-3 shadow-sm">
                        <h5>Add New Product</h5>
                        <form action="/add-product" method="POST" enctype="multipart/form-data">
                            <input name="n" placeholder="Product Name" class="form-control mb-2" required>
                            <input name="p" placeholder="Price (Rs)" class="form-control mb-2" required>
                            <select name="cat" class="form-select mb-2">{"".join([f'<option>{c}</option>' for c in CATEGORIES])}</select>
                            <input type="file" name="file" class="form-control mb-2" required>
                            <button class="btn btn-primary w-100">Upload & Save</button>
                        </form>
                    </div>
                </div>
                <div class="col-md-7">
                    <h5>Inventory Stock</h5>
                    <div style="max-height:400px; overflow-y:auto;">
                        <table class="table bg-white">
                            {{% for p in prods %}}
                            <tr><td><img src="{{{{p.img}}}}" width="40"></td><td>{{{{p.name}}}}</td><td>Rs.{{{{p.price}}}}</td><td><a href="/del-p/{{{{p._id}}}}">❌</a></td></tr>
                            {{% endfor %}}
                        </table>
                    </div>
                    <h5 class="mt-4">Registered Students (Leads)</h5>
                    <table class="table table-sm bg-white">
                        {{% for l in leads %}}
                        <tr><td>{{{{l.name}}}}</td><td>{{{{l.phone}}}}</td><td><a href="/del-l/{{{{l._id}}}}">🗑️</a></td></tr>
                        {{% endfor %}}
                    </table>
                </div>
            </div>
        </div>
    </body></html>
    ''', s=s, prods=prods, leads=leads)

# --- BACKEND LOGIC ---

@app.route('/update-settings', methods=['POST'])
def update_settings():
    if not session.get('logged_in'): return redirect('/admin')
    s = get_settings()
    data = {
        "shop_name": request.form.get('shop_name'),
        "announcement": request.form.get('announcement'),
        "group_link": request.form.get('group_link'),
        "logo_url": s['logo_url'],
        "poster_url": s['poster_url']
    }
    if 'logo' in request.files and request.files['logo'].filename != '':
        res = cloudinary.uploader.upload(request.files['logo'])
        data['logo_url'] = res['secure_url']
    if 'poster' in request.files and request.files['poster'].filename != '':
        res = cloudinary.uploader.upload(request.files['poster'])
        data['poster_url'] = res['secure_url']
    
    settings_col.update_one({"type": "config"}, {"$set": data}, upsert=True)
    return redirect('/admin')

@app.route('/clear-poster')
def clear_poster():
    settings_col.update_one({"type": "config"}, {"$set": {"poster_url": ""}})
    return redirect('/admin')

@app.route('/add-product', methods=['POST'])
def add_product():
    if not session.get('logged_in'): return redirect('/admin')
    res = cloudinary.uploader.upload(request.files['file'])
    inventory_col.insert_one({
        "name": request.form.get('n'), "price": request.form.get('p'),
        "cat": request.form.get('cat'), "img": res['secure_url'], "date": datetime.now()
    })
    return redirect('/admin')

@app.route('/del-p/<id>')
def del_p(id):
    inventory_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin')

@app.route('/del-l/<id>')
def del_l(id):
    leads_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin')

@app.route('/submit-review', methods=['POST'])
def submit_review():
    reviews_col.insert_one({"name": request.form.get('rev_name'), "review": request.form.get('rev_msg')})
    return redirect('/')

@app.route('/subscribe', methods=['POST'])
def subscribe():
    leads_col.insert_one({"name": request.form.get('n'), "phone": request.form.get('p'), "date": datetime.now()})
    return redirect(get_settings()['group_link'])

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/')

if __name__ == '__main__':
    app.run()
