import os
from flask import Flask, render_template, request, redirect
from pymongo import MongoClient

app = Flask(__name__)

# Connect to MongoDB
# We use an Environment Variable for safety!
mongo_uri = os.environ.get("MONGO_URI")
client = MongoClient(mongo_uri)
db = client['verma_pustak_db']
subscribers_col = db['subscribers']
reviews_col = db['reviews']

@app.route('/')
def home():
    # Fetch reviews from MongoDB instead of a text file
    reviews = list(reviews_col.find().sort("_id", -1))
    return render_template('index.html', reviews=reviews)

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email')
    if email:
        subscribers_col.insert_one({"email": email})
    return redirect('/')

@app.route('/review', methods=['POST'])
def review():
    name = request.form.get('name')
    text = request.form.get('review')
    if name and text:
        reviews_col.insert_one({"name": name, "review": text})
    return redirect('/')

if __name__ == "__main__":
    app.run()
