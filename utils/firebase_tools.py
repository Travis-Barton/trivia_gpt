import os
import toml
import firebase_admin
from firebase_admin import credentials, firestore

dir_path = os.path.dirname(os.path.realpath(__file__))
toml_path = os.path.join(dir_path, "../.streamlit/secrets.toml")

# Load data from the TOML file
toml_data = toml.load(toml_path)['google_auth']

# Extract the secret from Streamlit's secrets.toml
cred_dict = {
    'type': toml_data['type'],
    'project_id': toml_data['project_id'],
    'private_key_id': toml_data['private_key_id'],
    'private_key': toml_data['private_key'],
    'client_email': toml_data['client_email'],
    'client_id': toml_data['client_id'],
    'auth_uri': toml_data['auth_uri'],
    'token_uri': toml_data['token_uri'],
    'auth_provider_x509_cert_url': toml_data['auth_provider_x509_cert_url'],
    'client_x509_cert_url': toml_data['client_x509_cert_url'],
    # If there are more fields in your TOML data, add them here
}

cred = credentials.Certificate(cred_dict)

# Initialize the app if it doesn't exist
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)


def get_db():
    return firestore.client()
