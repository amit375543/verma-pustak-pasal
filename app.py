import os
import certifi
from flask import Flask
from pymongo import MongoClient

app = Flask(__name__)

# --- MINIMAL DATABASE TEST ---
try:
    # 1. Initialize SSL Certificate
    ca = certifi.where()

    # 2. Connection Logic
    mongo_uri = os.environ.get("MONGO_URI")
    client = MongoClient(
        mongo_uri, 
        tlsCAFile=ca, 
        tlsAllowInvalidCertificates=True, 
        serverSelectionTimeoutMS=5000
    )
    
    # Trigger a quick connection test
    client.admin.command('ping')
    db_status = "Successfully connected to MongoDB!"
except Exception as e:
    db_status = f"Database Connection Failed: {str(e)}"

@app.route('/')
def home():
    return f"<h1>Verma Pustak Pasal Test Page</h1><p>Status: {db_status}</p>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
