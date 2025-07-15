from flask import Flask, render_template, request, send_file
from dotenv import load_dotenv
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from io import BytesIO
import os
import csv
from datetime import datetime

# 🔐 Load AES key from .env
load_dotenv()
AES_KEY = os.getenv("AES_KEY").encode()

# 🛠️ Flask configuration
app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# 📊 Audit Logging Function
def log_event(action, filename):
    with open("event_log.csv", "a", newline="") as log:
        writer = csv.writer(log)
        writer.writerow([datetime.now(), action, filename])

# 🔒 AES Encryption Function
def encrypt_file(file_data):
    iv = get_random_bytes(16)
    cipher = AES.new(AES_KEY, AES.MODE_CFB, iv)
    encrypted_data = iv + cipher.encrypt(file_data)
    return encrypted_data

# 🔓 AES Decryption Function
def decrypt_file(encrypted_data):
    iv = encrypted_data[:16]
    cipher = AES.new(AES_KEY, AES.MODE_CFB, iv)
    decrypted_data = cipher.decrypt(encrypted_data[16:])
    return decrypted_data

# 📤 Upload & Encrypt Route
@app.route("/", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files["file"]
        if file:
            file_data = file.read()
            encrypted_data = encrypt_file(file_data)
            filename = file.filename + ".enc"
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            with open(save_path, "wb") as f:
                f.write(encrypted_data)
            log_event("upload", file.filename)
            msg = f"✅ File '{file.filename}' encrypted and saved!"
            files = [f for f in os.listdir(app.config["UPLOAD_FOLDER"]) if f.endswith(".enc")]
            return render_template("index.html", files=files, message=msg)

    files = [f for f in os.listdir(app.config["UPLOAD_FOLDER"]) if f.endswith(".enc")]
    return render_template("index.html", files=files)

# 📥 Download & Decrypt Route
@app.route("/download/<filename>")
def download(filename):
    encrypted_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(encrypted_path):
        with open(encrypted_path, "rb") as f:
            encrypted_data = f.read()
        decrypted_data = decrypt_file(encrypted_data)
        log_event("download", filename)
        return send_file(
            BytesIO(decrypted_data),
            download_name=filename.replace(".enc", ""),
            as_attachment=True
        )
    return "⚠️ File not found or decryption failed"

# 🚀 Launch Flask
if __name__ == "__main__":
    app.run(debug=True)