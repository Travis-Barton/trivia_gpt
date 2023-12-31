import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from utils.firebase_tools import get_db

from models.componants import Question, Answer

st.set_page_config(layout="wide",
                   page_title="Lets play Trivia",
                   page_icon="🎮",
)

db = get_db()


def main():
    st.title("Trivia Game")
    # Check URL parameters for game_id and team_name
    params = st.experimental_get_query_params()
    game_id_param = params.get("game_id", None)
    team_name_param = params.get("team_name", None)

    # Handle if there are no params
    if not game_id_param or not team_name_param:
        st.title("Oops! Seems like you've landed here before you've chosen a game to join.")
        st.link_button("click here to join a game!", url='https://join-trivia-game.streamlit.app/')
        st.stop()

    # If there are params, save them to the session state
    st.session_state.game_id = game_id_param[0]
    st.session_state.user_id = team_name_param[0]
    play, settings = st.tabs(['Play', 'Settings'])
    with settings:
        if st.button('Reset Game'):
            # Clear session state
            st.rerun()
    with play:
        # Welcome the team and display Game ID
        st.markdown(f"Welcome, __{st.session_state.user_id}!__")
        st.markdown(f"Using Game ID: __{st.session_state.game_id}__")

        if not db.collection(u'games').document(st.session_state.game_id).get().exists:
            st.warning("Please enter a valid Game ID to join the game.")
            st.stop()


    game_ref = db.collection(u'games').document(st.session_state.game_id)
    game = game_ref.get().to_dict()
    if st.session_state.user_id not in game['user_ids']:
        game_ref.update({
            'user_ids': firestore.ArrayUnion([st.session_state.user_id])
        })

    if st.button('Refresh Question'):
        st.rerun()
    # Display Open Questions
    # Fetch all questions for the game without sorting
    questions_ref = db.collection(u'questions').where(u'game_id', u'==', st.session_state.game_id).where(u'revealed',
                                                                                                         u'==',
                                                                                                         True).stream()
    open_questions = {doc.id: doc.to_dict() for doc in questions_ref}
    waiting_screen = game.get('waiting_screen', False)
    if not open_questions or waiting_screen:
        st.info("Waiting for questions...")
        # st.stop()
    else:
        # Sort questions locally based on 'order'
        latest_question_id = max(open_questions.keys(), key=lambda q_id: open_questions[q_id]['order'])
        latest_question = open_questions[latest_question_id]
        if latest_question['question'] == 'END||END||HOLD':
            st.info("Waiting for questions...")
            st.stop()
        st.markdown(f"**{latest_question['question']}**")

        # Check if user has already answered this question
        answered_already = db.collection(u'answers').where(u'user_id', u'==', st.session_state.user_id).where(
            u'question_id', u'==', latest_question_id).get()

        if not answered_already:
            user_answer = st.text_input(f"Your answer for: {latest_question['question']}",
                                        key=f"answer_{latest_question_id}",
                                        placeholder="Enter your answer here...",
                                        label_visibility='hidden')

            if st.button(f"Submit Your Final Answer", key=f"btn_{latest_question_id}"):
                if user_answer:
                    answer_ref = db.collection(u'answers').add({
                        'user_id': st.session_state.user_id,
                        'game_id': st.session_state.game_id,
                        'question_id': latest_question_id,
                        'answer': user_answer,
                        'timestamp': datetime.now(),
                        'graded': False,
                        'correct': False,
                    })
                    st.experimental_rerun()
                    st.success(f"Your answer for '{latest_question['question']}' has been submitted!")
                else:
                    st.warning("Please enter an answer before submitting.")
        else:
            st.info(
                f"You answered the question: \`{latest_question['question']}\` with: \`{answered_already[0].to_dict()['answer']}\`")

    # list all of their answers if any if answers have been revealed
    if game['show_answers']:
        st.markdown(f'Answers for {st.session_state.user_id}')
        answers_ref = db.collection(u'answers').where(u'user_id', u'==', st.session_state.user_id).where(
            u'game_id', u'==', st.session_state.game_id).stream()
        questions_ref = db.collection(u'questions').where(u'game_id', u'==', st.session_state.game_id).stream()
        questions = {doc.id: doc.to_dict() for doc in questions_ref}
        answers = {doc.id: doc.to_dict() for doc in answers_ref}
        sorted_questions = sorted(questions.items(), key=lambda x: x[1]['order'])
        # change the above to sort newest to oldest
        sorted_questions.reverse()
        for question_id, question_data in sorted_questions:
            if question_data['revealed']:
                show_rational = game.get('show_rational', False)

                col1, col2, col3 = st.columns(3) if not show_rational else st.columns((3, 1, 3))
                with col1:
                    st.markdown(f'**{question_data["question"]}**')
                associated_answer = next((answer_data for answer_id, answer_data in answers.items() if
                                          answer_data.get('question_id') == question_id), None)
                # from questions_ref
                actual_answer = next((answer_data for question_id, answer_data in questions.items() if
                                      question_id == question_id), None)
                with col2:
                    if associated_answer:
                        st.markdown(f'*{associated_answer["answer"].strip()}*')
                    else:
                        st.markdown(f'*No Answer*')
                with col3:
                    if show_rational:
                        if associated_answer:
                            st.markdown(f'*{"✅" if associated_answer["correct"] else "❌"}* ' +
                                        f'*{associated_answer["reason"].strip()}*')
                        else:
                            st.markdown(f'*No Answer*')
                    else:
                        if associated_answer:
                            st.markdown(f'*{"✅" if associated_answer["correct"] else "❌"}*')
                        else:
                            st.markdown(f'*No Answer*')


main()