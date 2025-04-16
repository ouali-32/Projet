from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from io import BytesIO
import qrcode
import base64
import os
import uuid
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from pyzbar.pyzbar import decode
from PIL import Image

app = Flask(__name__)
@app.route('/health')
def health():
    return "OK", 200

# Configuration MySQL Docker
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://qr_user:@localhost/qr_secure'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class QRCode(db.Model):
    __tablename__ = 'qr_codes'
    id = db.Column(db.String(36), primary_key=True)
    encrypted_data = db.Column(db.Text, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

# Chargement clé publique
# Remplacer le chemin par le chemin COMPLET vers public_key.pem
key_path = os.path.join(os.path.dirname(__file__), 'public_key.pem')
with open(key_path, 'rb') as f:
    public_key = serialization.load_pem_public_key(f.read(), backend=default_backend())

@app.route('/generate', methods=['POST'])
def generate_qr():
    data = request.json.get('data')
    if not data:
        return jsonify({"error": "Données manquantes"}), 400

    encrypted = public_key.encrypt(
        data.encode(),
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    encrypted_b64 = base64.urlsafe_b64encode(encrypted).decode()

    qr_id = str(uuid.uuid4())
    new_qr = QRCode(
        id=qr_id,
        encrypted_data=encrypted_b64,
        expires_at=datetime.utcnow() + timedelta(days=request.json.get('expiration_days', 30))
    )
    db.session.add(new_qr)
    db.session.commit()

    img = qrcode.make(f"{qr_id}||{encrypted_b64}")
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

@app.route('/verify', methods=['POST'])
def verify_qr():
    img = Image.open(request.files['file'].stream)
    qr_id, encrypted_b64 = decode(img)[0].data.decode().split('||')
    
    qr = QRCode.query.get(qr_id)
    if not qr or qr.encrypted_data != encrypted_b64:
        return jsonify({"error": "QR invalide"}), 400
    
    return jsonify({
        "status": "valid",
        "encrypted_data": encrypted_b64,
        "qr_id": qr_id
    })

with app.app_context():
    db.create_all()

if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port) 