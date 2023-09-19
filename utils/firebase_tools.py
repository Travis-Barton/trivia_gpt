import firebase_admin
from firebase_admin import credentials, firestore



cred = credentials.Certificate("trivia-gpt-backend-firebase.json")
firebase_admin.initialize_app(cred)


def get_firebase_db():
    db = firestore.client()
    return db

