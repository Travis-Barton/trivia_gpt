import streamlit as st

def main():
    question_tab, games_tab = st.tabs(["Questions", "Games"])
    with question_tab:
        st.header("Questions")
        file = st.file_uploader("Upload file", type=["csv"])
        if file is None:
            st.stop()
        st.write(file)
        cols = st.columns(2)
        with cols[0]:
            add_questions = st.button("Add Question")
        with cols[1]:
            add_categories = st.button("upload questions")

    with games_tab:
        st.header("Games")
        cols = st.columns(2)
        with cols[0]:
            add_games = st.button("Select Game")

        with cols[1]:
            game_state = st.button("Fetch Game State")
