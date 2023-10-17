import streamlit as st

st.set_page_config(
    page_title="Welcome to AI Trivia",
    page_icon="👋",
)

st.title("Welcome to Trivia GPT! 🎉")
st.subheader('A fun AI powered application that generates questions and grades answers in real-time with AI!')

col1, col2, col3 = st.columns(3)
with col1:
    st.title("Create Questions 📝")
    st.link_button(label="AI based question generation",
                   url='https://trivia-gpt.streamlit.app/')
with col2:
    st.title("Play as Trivia Master ✍️")
    st.link_button(label="Run a game with friends",
        url='https://trivia-gpt-gm.streamlit.app/')
with col3:
    st.title("Play as Participant 🎮")
    st.link_button(label="Join a game with friends",
        url='https://join-trivia-game.streamlit.app/')


st.markdown('Brought to you by [Travis Barton Consulting](https://www.travisbarton.com)')
