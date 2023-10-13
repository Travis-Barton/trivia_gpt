import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from utils.firebase_tools import get_db


db = get_db()
st.set_page_config(layout="wide")

def rerun_page():
    st.rerun()


def fetch_game_data(game_id):
    game_ref = db.collection(u'games').document(game_id)
    game_data = game_ref.get().to_dict()
    questions = [i.to_dict() for i in db.collection(u'questions').where(u'game_id', u'==', game_id).get()]
    # order by "order" field
    questions = sorted(questions, key=lambda x: x['order'])
    return game_data, questions


def main():
    if not st.session_state.get("current_question_index"):
        st.session_state.current_question_index = 0

    with st.sidebar:
        game_id_input = st.text_input('Enter Game ID:', key="game_id_input")

    if game_id_input:
        game_data, questions = fetch_game_data(game_id_input)

        if game_data:
            print(questions)
            question_ids = [i['question_id'] for i in questions]
            current_question_index = st.session_state.get("current_question_index", 0)

            # Display current question
            current_question = questions[current_question_index]
            st.subheader(f"Category: {current_question['category']}")
            st.title(current_question['question'])

            if st.session_state.get("reveal_answer", False):
                st.subheader(current_question['answer'])
            else:
                st.subheader("Answer: ???")

            # Buttons for navigating questions
            prev_button, next_button, set_timer, reveal_answer = st.columns(4)

            if prev_button.button("Prev") and current_question_index > 0:
                st.session_state.current_question_index -= 1
                st.session_state.reveal_answer = False
                st.rerun()

            if next_button.button("Next") and current_question_index < len(question_ids) - 1:
                st.session_state.current_question_index += 1
                st.session_state.reveal_answer = False
                st.rerun()


            if reveal_answer.button("Reveal Answer"):
                st.session_state.reveal_answer = True
                st.rerun()
            else:
                st.session_state.reveal_answer = False

            # Placeholder for setting a timer (can be expanded with actual functionality)
            if set_timer.button("Set Timer"):
                # Implement timer logic here
                pass

            # Reset the key event after processing
            st.session_state.key_event = None

            st.write(f"Question {current_question_index + 1} of {len(question_ids)}")

        else:
            st.write("Invalid Game ID.")
            st.session_state.pop("current_question_index", None)
            st.session_state.pop("reveal_answer", None)

if __name__ == '__main__':
    main()
