import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from models.componants import Question, Answer

# Firebase Initialization

db = firestore.client()
def main():
    st.set_page_config(layout="wide")
    if st.button('Fetch New Question'):
        st.experimental_rerun()

    # Session states
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'game_id' not in st.session_state:
        st.session_state.game_id = None

    # Join Game
    if not st.session_state.user_id:
        st.session_state.user_id = st.text_input("Enter Your Team Name:")
        if not st.session_state.user_id:
            st.warning("Please enter a team name to join the game.")
            st.stop()

    if not st.session_state.game_id:
        st.session_state.game_id = st.text_input("Enter Game ID:")
        if not st.session_state.game_id:
            st.warning("Please enter a valid Game ID to join the game.")
            st.stop()
    if not db.collection(u'games').document(st.session_state.game_id).get().exists:
        st.warning("Please enter a valid Game ID to join the game.")
        st.stop()

    game_ref = db.collection(u'games').document(st.session_state.game_id)
    game = game_ref.get().to_dict()
    if st.session_state.user_id not in game['user_ids']:
        game_ref.update({
            'user_ids': firestore.ArrayUnion([st.session_state.user_id])
        })

    # Display Open Questions
    # Fetch all questions for the game without sorting
    questions_ref = db.collection(u'questions').where(u'game_id', u'==', st.session_state.game_id).where(u'revealed',
                                                                                                         u'==',
                                                                                                         True).stream()
    open_questions = {doc.id: doc.to_dict() for doc in questions_ref}

    if not open_questions:
        st.info("Waiting for questions...")
        st.stop()

    # Sort questions locally based on 'order'
    latest_question_id = max(open_questions.keys(), key=lambda q_id: open_questions[q_id]['order'])
    latest_question = open_questions[latest_question_id]
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
        st.info(f"You answered the question: \`{latest_question['question']}\` with: \`{answered_already[0].to_dict()['answer']}\`")

    # list all of their answers if any if answers have been revealed
    if game['show_answers']:
        st.markdown(f'Answers for {st.session_state.user_id}')
        answers_ref = db.collection(u'answers').where(u'user_id', u'==', st.session_state.user_id).where(
            u'game_id', u'==', st.session_state.game_id).stream()
        questions_ref = db.collection(u'questions').where(u'game_id', u'==', st.session_state.game_id).stream()
        questions = {doc.id: doc.to_dict() for doc in questions_ref}
        answers = {doc.id: doc.to_dict() for doc in answers_ref}
        sorted_questions = sorted(questions.items(), key=lambda x: x[1]['order'])
        for question_id, question_data in sorted_questions:
            if question_data['revealed']:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f'**{question_data["question"]}**')
                associated_answer = next((answer_data for answer_id, answer_data in answers.items() if
                                          answer_data.get('question_id') == question_id), None)
                with col2:
                    if associated_answer:
                        st.markdown(f'*{associated_answer["answer"].strip()}*')
                    else:
                        st.markdown(f'*No Answer*')
                with col3:
                    if associated_answer:
                        st.markdown(f'*{"✅" if associated_answer["correct"] else "❌"}*')
                    else:
                        st.markdown(f'*No Answer*')


main()