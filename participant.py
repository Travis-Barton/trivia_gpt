import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
# from models.componants import Question, Answer
# import extra_streamlit_components as stx
from streamlitextras.cookiemanager import get_cookie_manager

from models.componants import Question, Answer
st.set_page_config(layout="wide",
                   page_title="Lets play Trivia",
                   page_icon="🎮",
)
db = firestore.client()
cookie_manager = None



def update_user_id(user_id):
    st.session_state.user_id = user_id




def main():
    play, settings = st.tabs(['Play', 'Settings'])
    # st.set_page_config(layout="wide")
    # if st.button('Fetch New Question'):
    #     st.info("Fetching new question...")
    #     st.experimental_rerun()
    #
    # # Session states
    # if 'user_id' not in st.session_state:
    #     st.session_state.user_id = None
    # if 'game_id' not in st.session_state:
    #     st.session_state.game_id = None
    #
    # # Join Game
    # if not st.session_state.user_id:
    #     st.session_state.user_id = st.text_input("Enter Your Team Name:")
    #     if not st.session_state.user_id:
    #         st.warning("Please enter a team name to join the game.")
    #         st.stop()
    # if 'game_id' not in st.session_state:
    #     st.session_state.game_id = None
    # if not st.session_state.game_id:
    #     st.session_state.game_id = st.text_input("Enter Game ID:", value=None)
    #     if not st.session_state.game_id:
    #         st.warning("Please enter a valid Game ID to join the game.")
    #         st.stop()

    global cookie_manager
    cookie_manager = get_cookie_manager()
    cookie_manager.delayed_init()  # Makes sure CookieManager stays in st.session_state

    with settings:
        # option to reset the game and start over with a new game_id and team name. Essentially nuke the cookies
        if st.button('Reset Game'):  # delete cookies
            cookie_manager.delete("game_id")
            cookie_manager.delete("team_name")
            st.rerun()
    with play:
        # Check if a team name is already saved in cookies
        team_name = cookie_manager.get("team_name")
        st.write(cookie_manager.cookies)
        if not team_name:
            team_name = st.text_input("Enter Your Team Name:", None)
            if team_name:
                # Set the team name as a cookie for 24 hours
                cookie_manager.set("team_name", team_name)
            else:
                st.info("Please enter a team name to join the game. 🍻")
                st.stop()
        else:
            st.markdown(f"Welcome, __{team_name}!__")

        game_id = cookie_manager.get("game_id")
        print(game_id)
        if not game_id:
            game_id = st.text_input("Enter Game ID:", value=None)
            print(f"game_id: {game_id}")
            if game_id:
                # Check the validity of the game_id (assuming you have a function or method for that)
                if db.collection(u'games').document(game_id).get().exists:
                    # Save game_id as a cookie for 24 hours
                    cookie_manager.set("game_id", game_id, key="game_id")
                else:
                    st.warning("Please enter a valid Game ID to join the game.")
                    st.stop()
        else:
            st.markdown(f"Using Game ID: __{game_id}__")
            # Update the session state with the game_id from the cookie
        if 'game_id' not in st.session_state:
            st.session_state.game_id = game_id
        if 'user_id' not in st.session_state:
            st.session_state.user_id = team_name
        # if not db.collection(u'games').document(st.session_state.game_id).get().exists:
        game_id = cookie_manager.get('game_id')
        user_id = cookie_manager.get('user_id')
        if not db.collection(u'games').document(game_id).get().exists:
            st.warning("Please enter a valid Game ID to join the game.")
            st.stop()

        game_ref = db.collection(u'games').document(game_id)
        game = game_ref.get().to_dict()
        if st.session_state.user_id not in game['user_ids']:
            game_ref.update({
                'user_ids': firestore.ArrayUnion([user_id])
            })

        # Display Open Questions
        # Fetch all questions for the game without sorting
        questions_ref = db.collection(u'questions').where(u'game_id', u'==', game_id).where(u'revealed',
                                                                                                             u'==',
                                                                                                             True).stream()
        open_questions = {doc.id: doc.to_dict() for doc in questions_ref}

        if not open_questions:
            st.info("Waiting for questions...")
            st.stop()

        # Sort questions locally based on 'order'
        latest_question_id = max(open_questions.keys(), key=lambda q_id: open_questions[q_id]['order'])
        latest_question = open_questions[latest_question_id]
        if latest_question['question'] == 'END||END||HOLD':
            st.info("Waiting for questions...")
            st.stop()
        st.markdown(f"**{latest_question['question']}**")

        # Check if user has already answered this question
        answered_already = db.collection(u'answers').where(u'user_id', u'==', user_id).where(
            u'question_id', u'==', latest_question_id).get()

        if not answered_already:
            user_answer = st.text_input(f"Your answer for: {latest_question['question']}",
                                        key=f"answer_{latest_question_id}",
                                        placeholder="Enter your answer here...",
                                        label_visibility='hidden')

            if st.button(f"Submit Your Final Answer", key=f"btn_{latest_question_id}"):
                if user_answer:
                    answer_ref = db.collection(u'answers').add({
                        'user_id': user_id,
                        'game_id': game_id,
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
            st.markdown(f'Answers for {user_id}')
            answers_ref = db.collection(u'answers').where(u'user_id', u'==', user_id).where(
                u'game_id', u'==', game_id).stream()
            questions_ref = db.collection(u'questions').where(u'game_id', u'==', game_id).stream()
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