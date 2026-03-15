from flask import Flask, request, redirect, render_template_string, url_for, session
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "verma_pustak_secret_key_2071" 

# --- FOLDER CONFIGURATION ---
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- PERSISTENT SETTINGS (Editable via Admin) ---
SETTINGS = {
    "shop_name": "Verma Pustak Pasal",
    "phone": "9779847299546",
    "fb_url": "https://www.facebook.com/verma.pustak.pasal",
    "announcement": "📢 NEW SESSION SALE: GET UP TO 10% OFF ON FULL BOOK SETS! VISIT US AT RAMGRAM-3, PARASI.",
    "map_html": '<iframe src="https://www.google.com/maps/embed?pb=!1m14!1m8!1m3!1d221.11605196570846!2d83.66632986997206!3d27.53590667892473!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3994268f8cfda139%3A0x41b745485bc55074!2sVerma%20Pustak%20Pasal!5e0!3m2!1sen!2snp!4v1773457457599!5m2!1sen!2snp" width="100%" height="380" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>',
    "logo_url": "/static/logo.png",
    "group_link": "https://chat.whatsapp.com/CAj5KOwL2EuAlmPQmOH5rX?mode=gi_t"
}

ADMIN_PASSWORD = "verma@123"
CATEGORIES = ["Textbooks", "Stationery", "Calculators", "Other"]

# --- INVENTORY DATA ---
INVENTORY = [
    {"id": 1, "name": "Class 10 Full Set", "price": "4800", "cat": "Textbooks", "img": "/static/logo.png", "desc": "Complete text books as per CDC syllabus.", "on_sale": True, "date_added": "2026-03-01"}
]

# --- UNIFIED CSS ---
SITE_CSS = f'''
<style>
    :root {{ 
        --primary: #2c3e50; --secondary: #25d366; --accent: #4f46e5;
        --bg: #f8fafd; --card-bg: white; --text: #333; --text-muted: #666;
        --greeting-color: #ff5722; 
    }}
    [data-theme="dark"] {{
        --primary: #1a1a1a; --secondary: #1db954; --accent: #818cf8;
        --bg: #121212; --card-bg: #1e1e1e; --text: #ffffff; --text-muted: #aaaaaa;
        --greeting-color: #ffeb3b;
    }}
    body {{ background: var(--bg); color: var(--text); font-family: 'Segoe UI', sans-serif; margin: 0; transition: 0.3s; padding-bottom: 20px; }}
    .announcement-bar {{ background: var(--secondary); color: white; padding: 12px; text-align: center; font-weight: 800; text-transform: uppercase; }}
    .header {{ background: var(--primary); color: white; padding: 40px 0 120px 0; text-align: center; border-bottom: 5px solid var(--secondary); }}
    .logo-box {{ background: white; display: inline-block; padding: 8px; border-radius: 15px; margin-bottom: 12px; width: 140px; box-shadow: 0 5px 20px rgba(0,0,0,0.3); overflow: hidden; }}
    .logo-img {{ width: 100%; height: auto; display: block; }}
    .theme-toggle {{ position: fixed; top: 15px; right: 15px; z-index: 3000; background: white; border: none; border-radius: 50%; width: 40px; height: 40px; cursor: pointer; box-shadow: 0 4px 10px rgba(0,0,0,0.2); display: flex; align-items: center; justify-content: center; }}
    .section-card {{ background: var(--card-bg); border-radius: 15px; padding: 35px; margin: -80px auto 40px auto; max-width: 1000px; box-shadow: 0 15px 35px rgba(0,0,0,0.15); position: relative; z-index: 10; }}
    .greeting-text {{ color: var(--greeting-color); font-weight: 800; font-size: 1.8rem; }}
    .product-card {{ background: var(--card-bg); border-radius: 15px; border: 1px solid rgba(0,0,0,0.05); overflow: hidden; transition: 0.3s; text-align: center; padding: 15px; position: relative; height: 100%; }}
    .product-card:hover {{ transform: translateY(-5px); box-shadow: 0 10px 25px rgba(0,0,0,0.1); }}
    .floating-sidebar {{ position: fixed; bottom: 30px; right: 20px; display: flex; flex-direction: column; gap: 12px; z-index: 2000; }}
    .side-icon {{ width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }}
    .side-icon img {{ width: 26px; height: 26px; filter: brightness(0) invert(1); }}
    footer {{ background: var(--primary); color: white; padding: 40px 0; text-align: center; margin-top: 60px; }}
</style>
'''

@app.route('/')
def home():
    hour = datetime.now().hour
    greeting = "Good Morning! ☀️" if hour < 12 else "Good Afternoon! 🌤️" if hour < 17 else "Good Evening! 🌙"
    selected_cat = request.args.get('category', 'All')
    search_q = request.args.get('search', '').lower()
    
    cat_btns = f'<a href="/" class="btn btn-sm btn-outline-primary m-1 {"active" if selected_cat == "All" else ""} text-dark">All</a>'
    for c in CATEGORIES:
        cat_btns += f'<a href="/?category={c}" class="btn btn-sm btn-outline-primary m-1 {"active" if selected_cat == c else ""} text-dark">{c}</a>'

    items_html = ""
    for p in INVENTORY:
        if (selected_cat == "All" or p['cat'] == selected_cat) and (search_q in p['name'].lower()):
            items_html += f'''
            <div class="col-md-4 mb-4">
                <div class="product-card shadow-sm">
                    <span class="badge bg-secondary mb-2">{p['cat']}</span>
                    <img src="{p['img']}" style="width:100%; height:150px; object-fit:contain;">
                    <h5 class="fw-bold mt-2">{p['name']}</h5>
                    <p class="small" style="color:var(--text-muted); min-height:40px;">{p['desc']}</p>
                    <p class="fw-bold fs-5" style="color:var(--accent);">Rs. {p['price']}</p>
                    <a href="https://wa.me/{SETTINGS['phone']}?text=Order: {p['name']}" class="btn btn-sm w-100 fw-bold text-white" style="background:var(--secondary); border-radius:50px; text-decoration:none; padding:10px;">Order on WhatsApp</a>
                </div>
            </div>'''

    reviews_html = ""
    if os.path.exists("reviews.txt"):
        with open("reviews.txt", "r") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) == 3:
                    reviews_html += f'<div style="background:rgba(0,0,0,0.03); padding:10px; border-radius:10px; margin-bottom:10px; text-align:left; border-left:4px solid var(--accent);"><strong>{parts[0]}</strong> <span style="color:#ffc107;">{"★"*int(parts[1])}</span><p class="mb-0 small">{parts[2]}</p></div>'

    return render_template_string(f'''
    <!DOCTYPE html>
    <html lang="en" data-theme="light">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{SETTINGS['shop_name']}</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">{SITE_CSS}</head>
    <body>
        <button class="theme-toggle" onclick="toggleTheme()">🌓</button>
        <div class="announcement-bar">{SETTINGS['announcement']}</div>
        <header class="header">
            <div class="logo-box"><img src="{SETTINGS['logo_url']}" class="logo-img"></div>
            <h1 class="fw-bold m-0">{SETTINGS['shop_name']}</h1>
            <p class="fs-6 mb-0 opacity-75">Ramgram-3, Parasi | 📞 {SETTINGS['phone']}</p>
        </header>

        <div class="floating-sidebar">
            <a href="{SETTINGS['group_link']}" target="_blank" class="side-icon" style="background:#25d366;"><img src="https://cdn-icons-png.flaticon.com/512/733/733585.png"></a>
            <a href="{SETTINGS['fb_url']}" target="_blank" class="side-icon" style="background:#1877f2;"><img src="https://cdn-icons-png.flaticon.com/512/733/733547.png"></a>
        </div>

        <div class="container">
            <div class="section-card text-center shadow-lg">
                <h2 class="greeting-text mb-1">{greeting}</h2>
                <form action="/subscribe" method="POST" class="row g-3 justify-content-center mt-3">
                    <div class="col-md-3"><input name="n" class="form-control" placeholder="Full Name" required></div>
                    <div class="col-md-3"><input name="p" class="form-control" placeholder="WhatsApp Number" required></div>
                    <div class="col-md-2"><input name="c" class="form-control" placeholder="Class" required></div>
                    <div class="col-md-2"><button type="submit" class="btn btn-dark w-100 fw-bold">JOIN GROUP</button></div>
                </form>
            </div>
            <div class="text-center mb-5">{cat_btns}</div>
            <div class="row">{items_html if items_html else "<p>No products found.</p>"}</div>
            <hr class="my-5">
            <div class="row">
                <div class="col-md-6 mb-5">
                    <h4 class="fw-bold mb-3">Our Location 📍</h4>
                    <div style="border-radius:15px; overflow:hidden; box-shadow:0 5px 15px rgba(0,0,0,0.1);">{SETTINGS['map_html']}</div>
                </div>
                <div class="col-md-6">
                    <h4 class="fw-bold mb-3">Customer Reviews</h4>
                    <div style="max-height:220px; overflow-y:auto; margin-bottom:20px;">{reviews_html if reviews_html else "<p class='small text-muted'>No reviews yet.</p>"}</div>
                    <form action="/submit-review" method="POST" class="bg-white p-3 border rounded shadow-sm">
                        <input name="rev_name" class="form-control form-control-sm mb-2" placeholder="Your Name" required>
                        <select name="rev_rating" class="form-control form-control-sm mb-2"><option value="5">★★★★★</option><option value="4">★★★★</option></select>
                        <textarea name="rev_msg" class="form-control form-control-sm mb-2" rows="2" placeholder="Message..." required></textarea>
                        <button type="submit" class="btn btn-sm btn-dark w-100">Submit Review</button>
                    </form>
                </div>
            </div>
        </div>
        <footer><p>© 2026 {SETTINGS['shop_name']} | <a href="/admin" style="color:white;">Admin Login</a></p></footer>
        <script>
            function toggleTheme() {{
                const body = document.documentElement;
                const newTheme = body.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
                body.setAttribute('data-theme', newTheme);
                localStorage.setItem('theme', newTheme);
            }}
            document.documentElement.setAttribute('data-theme', localStorage.getItem('theme') || 'light');
        </script>
    </body>
    </html>
    ''')

# --- PROFESSIONAL ADMIN DASHBOARD ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        if request.method == 'POST' and request.form.get('password') == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        return render_template_string('<body style="background:#2c3e50; display:flex; align-items:center; justify-content:center; height:100vh;"><form method="POST" style="background:white; padding:40px; border-radius:15px; width:300px; text-align:center;"><h3>Admin Access</h3><input type="password" name="password" placeholder="Password" style="width:100%; padding:10px; margin-bottom:20px; border:1px solid #ddd; border-radius:5px;"><button style="width:100%; background:#4f46e5; color:white; border:none; padding:10px; border-radius:5px; cursor:pointer;">Login</button></form></body>')

    leads = "".join([f"<tr><td>{l.strip()}</td><td class='text-end'><a href='/delete-lead/{i}' class='btn btn-sm btn-outline-danger'>Delete</a></td></tr>" for i, l in enumerate(open("subscribers.txt", "r"))]) if os.path.exists("subscribers.txt") else "<tr><td>No leads.</td></tr>"
    prod_rows = "".join([f"<tr><td><img src='{p['img']}' width='30'></td><td>{p['name']}</td><td>{p['desc']}</td><td>Rs.{p['price']}</td><td class='text-end'><a href='/delete-product/{p['id']}' class='btn btn-sm btn-danger'>X</a></td></tr>" for p in INVENTORY])
    rev_rows = "".join([f"<tr><td>{l.strip()[:30]}...</td><td class='text-end'><a href='/delete-review/{i}' class='btn btn-sm btn-outline-danger'>Delete</a></td></tr>" for i, l in enumerate(open("reviews.txt", "r"))]) if os.path.exists("reviews.txt") else "<tr><td colspan='2'>No reviews yet.</td></tr>"

    return render_template_string(f'''
    <!DOCTYPE html>
    <html><head><title>Admin Dashboard</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>body{{ background:#f0f2f5; padding:30px; }} .card{{ border-radius:12px; border:none; box-shadow:0 4px 10px rgba(0,0,0,0.05); margin-bottom:20px; }}</style></head>
    <body>
        <div class="container">
            <div class="d-flex justify-content-between align-items-center mb-4"><h2>Shop Management ⚙️</h2><a href="/logout" class="btn btn-danger">Logout</a></div>
            <div class="row">
                <div class="col-md-6">
                    <div class="card p-4">
                        <h5>Branding & Settings</h5>
                        <form action="/update-settings" method="POST" enctype="multipart/form-data">
                            <label class="small fw-bold">Shop Name</label><input name="shop_name" value="{SETTINGS['shop_name']}" class="form-control mb-2">
                            <label class="small fw-bold">WhatsApp No (Personal)</label><input name="phone" value="{SETTINGS['phone']}" class="form-control mb-2">
                            <label class="small fw-bold">WhatsApp Group Link</label><input name="group_link" value="{SETTINGS['group_link']}" class="form-control mb-2">
                            <label class="small fw-bold">Announcement Text</label><textarea name="announcement" class="form-control mb-2">{SETTINGS['announcement']}</textarea>
                            <label class="small fw-bold">Google Maps HTML Embed</label><textarea name="map_html" class="form-control mb-2" rows="3">{SETTINGS['map_html']}</textarea>
                            <label class="small fw-bold">Update Logo File:</label><input type="file" name="logo_file" class="form-control mb-3" accept="image/*">
                            <button class="btn btn-success w-100">Save All Changes</button>
                        </form>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card p-4">
                        <h5>Add Product</h5>
                        <form action="/add-product" method="POST" enctype="multipart/form-data">
                            <input name="n" placeholder="Product Name" class="form-control mb-2" required>
                            <input name="p" placeholder="Price" class="form-control mb-2" required>
                            <select name="cat" class="form-select mb-2">{"".join([f'<option>{c}</option>' for c in CATEGORIES])}</select>
                            <textarea name="d" placeholder="Description" class="form-control mb-2" required></textarea>
                            <input type="file" name="file" class="form-control mb-2" accept="image/*" required>
                            <button class="btn btn-primary w-100">Add to Stock</button>
                        </form>
                    </div>
                    <div class="card p-4">
                        <h5>Review Management</h5>
                        <table class="table table-sm table-hover"><tbody>{rev_rows}</tbody></table>
                    </div>
                </div>
                <div class="col-12">
                    <div class="card p-4"><h5>Inventory Stock</h5><table class="table table-hover table-sm"><thead><tr><th>Img</th><th>Name</th><th>Description</th><th>Price</th><th class="text-end">Action</th></tr></thead><tbody>{prod_rows}</tbody></table></div>
                    <div class="card p-4"><h5>Student Leads</h5><table class="table table-sm">{leads}</table></div>
                </div>
            </div>
        </div>
    </body></html>
    ''')

# --- HELPERS ---
@app.route('/update-settings', methods=['POST'])
def update_settings():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    SETTINGS['shop_name'] = request.form.get('shop_name')
    SETTINGS['phone'] = request.form.get('phone')
    SETTINGS['group_link'] = request.form.get('group_link')
    SETTINGS['announcement'] = request.form.get('announcement')
    SETTINGS['map_html'] = request.form.get('map_html')
    if 'logo_file' in request.files:
        file = request.files['logo_file']
        if file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            SETTINGS['logo_url'] = '/static/uploads/' + filename
    return redirect(url_for('admin'))

@app.route('/add-product', methods=['POST'])
def add_product():
    if not session.get('logged_in'): return redirect(url_for('admin'))
    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        img_url = '/static/uploads/' + filename
        INVENTORY.append({
            "id": len(INVENTORY)+1, "name": request.form.get('n'), "price": request.form.get('p'),
            "cat": request.form.get('cat'), "img": img_url, "desc": request.form.get('d'),
            "on_sale": False, "date_added": datetime.now().strftime('%Y-%m-%d')
        })
    return redirect(url_for('admin'))

@app.route('/delete-product/<int:p_id>')
def delete_product(p_id):
    if not session.get('logged_in'): return redirect(url_for('admin'))
    global INVENTORY
    INVENTORY = [p for p in INVENTORY if p['id'] != p_id]
    return redirect(url_for('admin'))

@app.route('/delete-review/<int:index>')
def delete_review(index):
    if not session.get('logged_in'): return redirect(url_for('admin'))
    if os.path.exists("reviews.txt"):
        lines = open("reviews.txt", "r").readlines()
        if 0 <= index < len(lines):
            del lines[index]
            with open("reviews.txt", "w") as f: f.writelines(lines)
    return redirect(url_for('admin'))

@app.route('/delete-lead/<int:index>')
def delete_lead(index):
    if not session.get('logged_in'): return redirect(url_for('admin'))
    if os.path.exists("subscribers.txt"):
        lines = open("subscribers.txt", "r").readlines()
        if 0 <= index < len(lines):
            del lines[index]
            with open("subscribers.txt", "w") as f: f.writelines(lines)
    return redirect(url_for('admin'))

@app.route('/submit-review', methods=['POST'])
def submit_review():
    n, r, m = request.form.get('rev_name'), request.form.get('rev_rating'), request.form.get('rev_msg').replace('|', '-')
    with open("reviews.txt", "a") as f: f.write(f"{n}|{r}|{m}\n")
    return redirect(url_for('home'))

@app.route('/subscribe', methods=['POST'])
def subscribe():
    n, p, c = request.form.get('n'), request.form.get('p'), request.form.get('c')
    with open("subscribers.txt", "a") as f: f.write(f"{n} | {p} | Class {c}\n")
    return redirect(SETTINGS['group_link'])

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)