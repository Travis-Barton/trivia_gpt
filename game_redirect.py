import streamlit as st

BASE_URL = "https://trivia-gpt-participant.streamlit.app/"

def validate_game_id(game_id):
    # Placeholder function for game_id validation
    # TODO: Add your actual validation logic here.
    # For example, checking the game_id against a database.
    return True

def main():
    st.title("Game Redirect")

    # Collect user_id and game_id from the user
    user_id = st.text_input("Enter Your Team Name:")
    game_id = st.text_input("Enter Game ID:")

    # Validate game_id
    if user_id and game_id:
        if validate_game_id(game_id):
            redirect_url = f"{BASE_URL}?team_name={user_id}&game_id={game_id}"
            st.markdown(f'<a href="{redirect_url}" target="_blank"><button>Join Game</button></a>', unsafe_allow_html=True)
        else:
            st.warning("Please enter a valid Game ID.")

if __name__ == "__main__":
    main()
