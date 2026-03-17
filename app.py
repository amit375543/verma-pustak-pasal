import os
import certifi # Ensure this is in your requirements.txt
from flask import Flask
from pymongo import MongoClient

app = Flask(__name__)

# --- FIX START ---
# Define 'ca' BEFORE initializing the MongoClient
ca = certifi.where() 

mongo_uri = os.environ.get("MONGO_URI")
client = MongoClient(
    mongo_uri, 
    tlsCAFile=ca, 
    tlsAllowInvalidCertificates=True, 
    connect=False
)
db = client['verma_pustak_db']
# --- FIX END ---

@app.route('/')
def home():
    return "<h1>Verma Pustak Pasal is Live!</h1>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
