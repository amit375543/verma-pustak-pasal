import os
import certifi
from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from datetime import datetime
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app.secret_key = "verma_secret_key" # Change this for security

# --- DATABASE & CLOUD CONFIG ---
ca = certifi.where()
client = MongoClient(
    os.environ.get("MONGO_URI"),
    tlsCAFile=ca,
    tlsAllowInvalidCertificates=True,
    connect=False
)
db = client['verma_pustak_db']
books_collection = db['books']

cloudinary.config(
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key = os.environ.get("CLOUDINARY_API_KEY"),
    api_secret = os.environ.get("CLOUDINARY_API_SECRET")
)

# --- ROUTES ---

@app.route('/')
def index():
    # Fetch all books from database
    books = list(books_collection.find().sort("created_at", -1))
    return render_template('index.html', books=books)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        title = request.form.get('title')
        price = request.form.get('price')
        file_to_upload = request.files.get('image')
        
        if file_to_upload:
            upload_result = cloudinary.uploader.upload(file_to_upload)
            image_url = upload_result['secure_url']
            
            books_collection.insert_one({
                "title": title,
                "price": price,
                "image_url": image_url,
                "created_at": datetime.now()
            })
            flash("Book added successfully!")
            return redirect(url_for('index'))
            
    return render_template('admin.html')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
