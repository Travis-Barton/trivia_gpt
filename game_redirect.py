import streamlit as st
from utils.firebase_tools import get_db

st.set_page_config(page_title="Game Redirect", page_icon="🎮")


db = get_db()


BASE_URL = "https://trivia-gpt-participant.streamlit.app/"


def validate_game_id(game_id):
    if not db.collection(u'games').document(game_id).get().exists:
        return False
    return True


def main():
    st.title("Game Redirect")

    # Collect user_id and game_id from the user
    user_id = st.text_input("Enter Your Team Name:", key="user_id")
    game_id = st.text_input("Enter Game ID:", key="game_id")

    # Validate game_id
    if user_id and game_id:
        if validate_game_id(game_id):
            redirect_url = f"{BASE_URL}?team_name={user_id}&game_id={game_id}"
            st.link_button("Click here to join the game!", url=redirect_url)
        else:
            st.warning("Please enter a valid Game ID.")


if __name__ == "__main__":
    main()
