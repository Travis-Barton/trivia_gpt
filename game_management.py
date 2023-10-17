import pandas as pd
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
from datetime import datetime
from models.componants import Question, Answer, Game
from utils.firebase_tools import get_db
import string
import random as rd
db = get_db()


ANIMALS = [
    "Bat", "Bee", "Boar", "Cat", "Dog", "Elk", "Fox", "Goat", "Hen", "Koi",
    "Lion", "Moth", "Owl", "Pig", "Rat", "Toad", "Wolf", "Yak", "Zebu", "Crow",
    "Bear", "Mule", "Lynx", "Eel", "Crab", "Dove", "Frog", "Goose", "Hare", "Jay",
    "Kiwi", "Lemur", "Mink", "Newt", "Orca", "Puma", "Dolphin", "Rhea", "Seal", "Tuna",
    "Shark", "Vole", "Wasp", "Emu", "Yabby", "Zorse", "Eagle", "Finch", "Guppy", "Puppy"
]
BEER_TYPES = [
    "Ale", "Lager", "Stout", "Malt", "Porter", "Pilsner", "Bock", "Wheat", "Sour", "Amber",
    "Blonde", "Brown", "Cream", "Dark", "Dunkel", "Fruit", "Golden", "Honey", "India Pale", "Light",
    "Mead", "Mild", "Old", "Pale", "Red", "Rye", "Scotch", "Strong", "Tripel", "Vienna",
    "Barleywine", "Berliner", "Seltzer", "Black", "Brett", "Double", "Dry", "Dubbel", "Eisbock", "Gose",
    "Helles", "Kolsch", "Lambic", "Marzen", "Oatmeal", "Quadrupel", "Rauchbier", "Saison", "Trappist", "Witbier"
]

def generate_3_digit_code():
    choices = string.digits
    return ''.join(rd.choice(choices) for _ in range(3))


def check_combination_exists(combination):
    games_ref = db.collection('games')
    # Query for the specific combination
    results = games_ref.where('game_id', '==', combination).limit(1).get()

    # If any results are returned, the combination exists
    return len(results) > 0


def generate_game_id():
    animal = rd.choice(ANIMALS)
    beer = rd.choice(BEER_TYPES)
    code = generate_3_digit_code()
    combination = f"{animal}{beer}{code}"

    if check_combination_exists(combination):
        return generate_game_id()
    return combination


def invert_question_status(question_id):
    question_ref = db.collection(u'questions').document(question_id)
    question = question_ref.get().to_dict()
    question_ref.update({
        'revealed': not question['revealed'],
        'modified_at': datetime.now()
    })


def sync_with_firestore(updated_board, old_board):
    if not st.session_state.get("initialized"):
        st.session_state.initialized = True
        st.session_state.old_board = old_board

    # Check for changes before invoking the comparison function
    if not updated_board.equals(old_board):
        handle_change(updated_board, old_board)
        st.session_state.old_board = updated_board.copy()


def handle_change(updated_board, old_board):
    for team in updated_board.columns:
        for question_text in updated_board.index:
            question_id = get_question_id_from_text(question_text)
            if updated_board.loc[question_text, team] != old_board.loc[question_text, team]:
                update_answer(question_id, team, updated_board.loc[question_text, team])


def get_question_id_from_text(question_text):
    questions_ref = db.collection(u'questions')
    return questions_ref.where(u'question', u'==', question_text).where(u'game_id', u'==', st.session_state.game_id).get()[0].id


def update_answer(question_id, team, new_value):
    answers_ref = db.collection(u'answers')
    answer_query = answers_ref.where(u'question_id', u'==', question_id).where(u'user_id', u'==', team).get()
    if answer_query:
        answer_id = answer_query[0].id
        answers_ref.document(answer_id).update({
            'correct': bool(new_value)
        })

def main():
    st.set_page_config(layout="wide",
                       page_title="Trivia Game Management",
                       page_icon="✍️")

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

            game_id = generate_game_id()
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
                    'waiting_screen': False,
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

    if 'waiting_screen' not in st.session_state:
        st.session_state.waiting_screen = False
    # Fetch all questions for the game at once
    questions = questions_ref.where('game_id', '==', st.session_state.game_id).stream()
    questions_list = [q.to_dict() for q in questions]

    questions_list.sort(key=lambda x: x['order'])
    # Open Questions
    # col1, col2, col3 = st.columns(3)
    for question in questions_list:
        question_id = question['question_id']

        # with col1 if idx % 3 == 0 else col2 if idx % 3 == 1 else col3:
        question = questions_ref.document(question_id).get().to_dict()
        if question_id not in st.session_state.toggle_states:
            st.session_state.toggle_states[question_id] = question['revealed']
        new_toggle_state = st.toggle(f"{question['order']+1}: {question['question']}", key=question_id,
                                     value=st.session_state.toggle_states[question_id],
                                     help=question['answer'])
        # Update the toggle state in session_state and Firestore if changed
        if new_toggle_state != st.session_state.toggle_states[question_id]:
            st.session_state.toggle_states[question_id] = new_toggle_state
            invert_question_status(question_id)

    if st.button('update participants'):
        # refresh the participants list
        # game_ref = db.collection(u'games').document(st.session_state.game_id)
        st.experimental_rerun()
    col_left, col_right = st.columns(2)
    with col_left:
        st.session_state.show_answers = st.checkbox('Show Answers', value=st.session_state.show_answers)
    with col_right:
        st.session_state.waiting_screen = st.checkbox('Waiting Screen', value=st.session_state.waiting_screen)

    game_leaderboards, edit_player_scores, game_pace_control = st.tabs(['Leaderboards',
                                                                        'Edit Player Scores',
                                                                        'Game Pace Control'])
    # Update the database based on the checkbox state
    game_ref = db.collection(u'games').document(st.session_state.game_id)
    game_ref.update({
        'show_answers': st.session_state.show_answers
    })
    game_ref.update({
        'waiting_screen': st.session_state.waiting_screen
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
            st.markdown('**Edit Player Scores**')
            # Initial load of the scoreboard into session state if it doesn't exist
            if 'board_value' not in st.session_state:
                st.session_state.board_value = Game.get_scoreboard(st.session_state.game_id)
            # Update the session state board to include any new participants
            # Get the latest board from the game
            board = Game.get_scoreboard(st.session_state.game_id)
            # Show the data editor for the board and capture any modifications
            new_board = st.data_editor(board, use_container_width=True)
            # Use the `sync_with_firestore` function to manage board changes and session state
            sync_with_firestore(new_board, board)


main()
