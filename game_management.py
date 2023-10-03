import pandas as pd
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
from datetime import datetime
from models.componants import Question, Answer, Game
from utils.firebase_tools import get_db

db = get_db()


def invert_question_status(question_id):
    question_ref = db.collection(u'questions').document(question_id)
    question = question_ref.get().to_dict()
    question_ref.update({
        'revealed': not question['revealed'],
        'modified_at': datetime.now()
    })


def handle_change(updated_board):
    # The function logic to handle changes can be placed here.
    for team in updated_board.columns:
        for question_text in updated_board.index:
            question_id = get_question_id_from_text(question_text, db.collection(u'questions'))
            if updated_board[team][question_text] != st.session_state.board_value[team][question_text]:
                update_answer(question_id, team, updated_board[team][question_text])


def get_question_id_from_text(question_text, questions_ref):
    # This can be optimized if you can cache these values or if there's a better way to retrieve them
    return questions_ref.where(u'question', u'==', question_text).get()[0].id


def update_answer(question_id, team, new_value):
    answer_ref = db.collection(u'answers').where(u'question_id', u'==', question_id).where(u'user_id', u'==', team).get()
    if answer_ref:
        answer_ref = answer_ref[0].id
        db.collection(u'answers').document(answer_ref).update({
            'correct': new_value
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
                    # 'correct': False,
                    'order': idx,
                })

            # Set up new game
            game_ref = db.collection(u'games').document(game_id)
            game_ref.set({
                'game_id': game_id,
                'user_ids': [],
                'question_ids': question_ids,
                'show_answers': False,
                'created_at': datetime.now(),
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

    game_leaderboards, edit_player_scores = st.tabs(['Leaderboards', 'Edit Player Scores'])
    # Update the database based on the checkbox state
    game_ref = db.collection(u'games').document(st.session_state.game_id)
    game_ref.update({
        'show_answers': st.session_state.show_answers
    })
    check_all_answers_graded = Game.check_all_answers_graded(st.session_state.game_id)
    if check_all_answers_graded:
        st.success('All answers have been graded!')
    else:
        st.warning('Not all answers have been graded yet.')
    with game_leaderboards:
        leaderboard = Game.get_leaderboard(st.session_state.game_id)
        st.dataframe(leaderboard, width=600)
    with edit_player_scores:
        game = game_ref.get().to_dict()
        user_ids = game['user_ids']
        col1, col2 = st.columns(2)
        with col1:
            st.json(Game.get_user_answers(st.session_state.game_id))
        with col2:
            st.markdown('**Edit Player Scores**\n(not currently functional)')
            if 'board_value' not in st.session_state:
                st.session_state.board_value = Game.get_scoreboard(st.session_state.game_id)
            board = Game.get_scoreboard(st.session_state.game_id)

            new_board = st.data_editor(board, use_container_width=True)
            if new_board.to_json() != board.to_json():
                handle_change(new_board)
                st.session_state.board_value = new_board


main()
