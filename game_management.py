import pandas as pd
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
from datetime import datetime

# Firebase Initialization
cred = credentials.Certificate("trivia-gpt-db.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

def invert_question_status(question_id):
    question_ref = db.collection(u'questions').document(question_id)
    question = question_ref.get().to_dict()
    question_ref.update({
        'revealed': not question['revealed'],
        'modified_at': datetime.now()
    })

def main():
    st.set_page_config(layout="wide")

    # Initialize these references and variables at the top
    questions_ref = db.collection(u'questions')
    game_ref = None
    question_ids = []

    st.write(f'**Game ID:** {st.session_state.get("game_id", None)}')
    data_upload = st.file_uploader("Game Data", type=['csv', 'xlsx'])
    new_game, existing_game = st.tabs(['New Game', 'Existing Game'])

    with new_game:
        if data_upload and st.button('Start Game'):
            if 'csv' in data_upload.type:
                df = pd.read_csv(data_upload)
            elif 'xlsx' in data_upload.type:
                df = pd.read_excel(data_upload)

            game_id = str(uuid.uuid4())
            st.session_state.game_id = game_id
            # Iteratively add questions and keep track of their IDs
            for idx, row in df.iterrows():
                question_id = str(uuid.uuid4())
                question_ids.append(question_id)
                questions_ref.document(question_id).set({
                    'question': row['question'],
                    'answer': row['answer'],
                    'category': row['category'],
                    'game_id': game_id,
                    'question_id': question_id,
                    'revealed': False,
                    'created_at': datetime.now(),
                    'modified_at': datetime.now(),
                    'correct': False,
                    'order': idx,
                })

            # Set up new game
            game_ref = db.collection(u'games').document(game_id)
            game_ref.set({
                'game_id': game_id,
                'user_ids': [],
                'question_ids': question_ids,
                'show_answers': False,
            })
            st.write(f'Game {game_id} Started')

    with existing_game:
        game_id_input = st.text_input('Enter Game ID', value=st.session_state.get('game_id', ''))
        if game_id_input:
            st.session_state.game_id = game_id_input
            game_ref = db.collection(u'games').document(game_id_input)
            game_data = game_ref.get().to_dict()
            question_ids = game_data.get('question_ids', [])
            st.write(f"Loaded Game ID: {game_id_input}")

    if not question_ids:
        st.warning('No questions found. Please start a new game or enter a valid Game ID.')
        st.stop()
    # Initialization of toggle states if not exists
    if 'toggle_states' not in st.session_state:
        st.session_state.toggle_states = {}

    if 'show_answers' not in st.session_state:
        st.session_state.show_answers = False  # Initialize with a default value

    # Open Questions
    col1, col2, col3 = st.columns(3)
    for idx, question_id in enumerate(question_ids):

        with col1 if idx % 3 == 0 else col2 if idx % 3 == 1 else col3:
            question = questions_ref.document(question_id).get().to_dict()
            if question_id not in st.session_state.toggle_states:
                st.session_state.toggle_states[question_id] = question['revealed']
            new_toggle_state = st.toggle(question['question_id'], key=question_id,
                                         value=st.session_state.toggle_states[question_id],
                                         help=question['answer'])
            # Update the toggle state in session_state and Firestore if changed
            if new_toggle_state != st.session_state.toggle_states[question_id]:
                st.session_state.toggle_states[question_id] = new_toggle_state
                invert_question_status(question_id)

    if st.button('update participants'):
        # refresh the participants list
        game_ref = db.collection(u'games').document(st.session_state.game_id)
    st.session_state.show_answers = st.checkbox('Show Answers', value=st.session_state.show_answers)

    # Update the database based on the checkbox state
    game_ref = db.collection(u'games').document(st.session_state.game_id)
    game_ref.update({
        'show_answers': st.session_state.show_answers
    })

    game = game_ref.get().to_dict()
    user_ids = game['user_ids']
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('**Participants**')
        for user_id in user_ids:
            st.write(user_id)
    with col2:
        st.markdown('**Leaderboard**')
        pass  # pass for now
    # You'd need to retrieve and display data based on your game and response structure


main()
