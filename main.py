import streamlit as st
import pandas as pd
from utils.language_model_tools import fact_check_question, question_generator, fix_question, grade_responses
from langchain.callbacks import StreamlitCallbackHandler
import streamlit_survey as ss
st.set_page_config(layout="wide")

# @st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')


def clear_cache():
    st.session_state.data = pd.DataFrame()


def main():
    if "data" not in st.session_state:
        st.session_state.data = pd.DataFrame()

    with st.sidebar:
        st.title("Download the questions template")
        df = pd.DataFrame(columns=['questions', 'answers', 'category'])
        st.download_button(
            label="Download data as CSV",
            data=convert_df(df),
            file_name='questions_template.csv',
            mime='text/csv',
        )
        st.write('---')
        st.title("Try a Demo data set")
        demo = pd.read_csv('demo.csv', index_col=0)
        st.download_button(
            label="Download data as CSV",
            data=convert_df(demo),
            file_name='questions_template.csv',
            mime='text/csv',
        )
        st.write('---')
    question_tab, games_tab, how_to_use = st.tabs(["Questions", "Games", "How to use"])
    with question_tab:
        st.header("Questions")
        with st.sidebar:
            st.title("Settings ⚙️")
            hide_answers = st.checkbox("hide questions", value=False)
        if st.checkbox('Use Your Own Data'):
            file = st.file_uploader("Upload file", type=["csv"], on_change=clear_cache)
            if file is None:
                st.stop()
            if (st.session_state.data.empty):
                st.session_state.data = pd.read_csv(file, index_col=False)

            with st.sidebar:
                fact_check_button = st.button("Run AI Fact-Check")
            if fact_check_button:
                with st.status("Fact checking questions...", expanded=True, state='running') as status:
                    for i, row in st.session_state.data.iterrows():
                        response_dict = fact_check_question(row.question, row.answer, row.category)
                        status.update(label=f"Fact checking questions... {i+1}/{len(st.session_state.data)}", state='running')
                        if response_dict['fact_check']:
                            st.session_state.data.loc[i, 'fact_check'] = response_dict['fact_check']
                            st.session_state.data.loc[i, 'explanation'] = ""
                        else:
                            st.session_state.data.loc[i, 'fact_check'] = response_dict['fact_check']
                            st.session_state.data.loc[i, 'explanation'] = response_dict['explanation']
        else:
            catagories = st.text_input("Enter Categories seperated by a comma")
            catagories = catagories.split(',')
            catagories = [cat.strip() for cat in catagories if cat.strip() != '']
            if len(catagories) > 5:
                st.warning('catagories are currently limited to 5')
                catagories = catagories[:5]
            col1, col2 = st.columns(2)
            with col1:
                question_count = st.number_input("Enter number of questions per category", value=4, max_value=10, min_value=1)
            with col2:
                difficulty = st.selectbox("Select Difficulty", ['Hard', 'Medium', 'Easy'])
            if st.session_state.data.empty:
                st.session_state.data = pd.read_csv('template.csv')
            cols = st.columns(2)
            if st.button("Generate Questions"):
                with st.status("Preparing data...", expanded=True, state='running') as status:
                    st.write('Generating questions...')
                    result = question_generator(categories=catagories, question_count=question_count, difficulty=difficulty, st_status=status)
                    for category, questions in result.items():
                        _ = pd.json_normalize(questions)
                        if len(_) > question_count:
                            _ = _.sample(question_count)
                        _['category'] = category
                        st.session_state.data = pd.concat([st.session_state.data, _], axis=0)
                    st.session_state.data = st.session_state.data.dropna(how='all')
                    st.session_state.data = st.session_state.data.reset_index(drop=True)
                    st.session_state.data = st.session_state.data[['question', 'answer', 'category']]
                    st.session_state.data['fact_check'] = None
                    st.write('Fact checking questions...')
                    for i, row in st.session_state.data.iterrows():
                        response_dict = fact_check_question(row.question, row.answer, row.category)
                        status.update(label=f"Fact checking questions... {i+1}/{len(st.session_state.data)}", state='running')
                        if response_dict['fact_check']:
                            st.session_state.data.loc[i, 'fact_check'] = response_dict['fact_check']
                            st.session_state.data.loc[i, 'explanation'] = ""
                        else:
                            st.session_state.data.loc[i, 'fact_check'] = response_dict['fact_check']
                            st.session_state.data.loc[i, 'explanation'] = response_dict['explanation']
            else:
                print(st.session_state.data)


        if ('fact_check' in st.session_state.data.columns) and any(st.session_state.data.fact_check == False):
            st.warning("Some questions failed fact checking. Please review the questions and answers.")
        if hide_answers:
            temp_data = st.session_state.data.copy()
            temp_data['answer'] = 'xxx'
            temp_data['question'] = 'xxx'
            temp_data['explanation'] = 'xxx'
            st.dataframe(temp_data)
        else:
            st.session_state.data = st.data_editor(st.session_state.data, use_container_width=True)
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="Download data as CSV",
                data=convert_df(st.session_state.data),
                file_name='questions.csv',
                mime='text/csv',
            )
        with col2:
            with st.sidebar:
                replace_button = st.button('AI Fix Answers')
            if replace_button:
                with st.status("Finding new questions...", expanded=True, state='running') as status:
                    for i, row in st.session_state.data.iterrows():
                        if not row.fact_check:
                            st.write(f'fixing question {i+1}')
                            response_dict = fix_question(row.question, row.answer, row.category, row.explanation,
                                                         st.session_state.data.question.tolist())
                            st.session_state.data.loc[i, 'question'] = response_dict['question']
                            st.session_state.data.loc[i, 'answer'] = response_dict['answer']
                            st.session_state.data.loc[i, 'category'] = response_dict['category']
                            st.session_state.data.loc[i, 'explanation'] = response_dict['explanation']
                            st.session_state.data.loc[i, 'fact_check'] = response_dict['fact_check']
                            # refresh page
                    st.experimental_rerun()

    with games_tab:

        st.title("Lets Play Trivia!")
        st.write('---')
        if st.session_state.data.empty:
            st.warning("Please upload or generate questions first.")
        else:

            survey = ss.StreamlitSurvey()
            with st.sidebar:
                if st.button('Reset Game'):  # delete self.data_name not in st.session_state: from session state
                    st.session_state.data_name = None
                    st.session_state[survey.data_name] = {}
                    pages = survey.pages(len(st.session_state.data), on_submit=lambda: grade_responses(survey.to_json()))
            pages = survey.pages(len(st.session_state.data), on_submit=lambda: grade_responses(survey.to_json()))
            with pages:
                page_count = pages.current
                question = st.session_state.data.loc[page_count, 'question']
                answer = st.session_state.data.loc[page_count, 'answer']
                category = st.session_state.data.loc[page_count, 'category']
                st.markdown(f"Question {page_count+1}/{len(st.session_state.data)}")
                st.write(st.session_state.data.loc[page_count, 'question'])
                st.write('---')
                survey.text_input(label=f"{question} || {answer} || {category}",
                                  label_visibility='collapsed')
                st.write('---')

    with how_to_use:
        st.title("How to use")



if __name__ == "__main__":
    main()
