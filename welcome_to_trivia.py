import streamlit as st


st.title("Welcome to Trivia! 🎉")
st.subheader('A fun AI power application that generates questions and grades answers in real-time!')

col1, col2, col3 = st.columns(3)
with col1:
    st.title("Create Questions 📝")
    st.link_button(label="AI based question generation",
                   url='https://trivia-gpt.streamlit.app/')
with col2:
    st.title("Play as Trivia Master 🎮")
    st.link_button(label="Run a game with friends",
        url='https://trivia-gpt-gm.streamlit.app/')
with col3:
    st.title("Play as Participant 🎮")
    st.link_button(label="Join a game with friends",
        url='https://trivia-gpt-participant.streamlit.app/')


st.markdown('Brought to you by [Travis Barton Consulting](travisbarton.com)')