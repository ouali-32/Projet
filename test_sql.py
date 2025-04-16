import os
import requests
from decryptor import decrypt,load_private_key
Mot = "Ouali Baleh"
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
TEST_DATA =  Mot

def test_generation():
    print("=== Test Génération QR ===")
    response = requests.post(f"{BASE_URL}/generate", json={"data": TEST_DATA})
    if response.status_code != 200:
        print(f"❌ Erreur: {response.text}")
        return False
    
    with open("test_qr.png", "wb") as f:
        f.write(response.content)
    print("✅ QR généré")
    return True

def test_verification():
    print("\n=== Test Vérification ===")
    try:
        with open("test_qr.png", "rb") as f:
            response = requests.post(f"{BASE_URL}/verify", files={"file": f})
        
        if response.status_code != 200:
            print(f"❌ Erreur: {response.text}")
            return False
        
        data = response.json()
        private_key = load_private_key()
        decrypted = decrypt(data['encrypted_data'], private_key)
        print(f"✅ Données déchiffrées : {decrypted}")
        return decrypted == TEST_DATA

    except Exception as e:
        print(f"❌ Crash: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_generation() and test_verification()
    print(f"\nRésultat final : {'✅' if success else '❌'}")
    