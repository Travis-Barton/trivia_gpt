import os
from typing import List, Dict, Union
import streamlit as st
import pandas as pd
from langchain.chat_models import ChatOpenAI
from langchain.agents import Tool
from langchain.chains import LLMChain
from langchain.utilities import BingSearchAPIWrapper
from typing import List
import toml
from langchain.agents import initialize_agent, AgentType, Tool, LLMSingleActionAgent, AgentExecutor, AgentOutputParser
from langchain.chains import LLMMathChain
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI
from langchain.utilities import SerpAPIWrapper, SQLDatabase
from langchain.prompts import ChatPromptTemplate
from langchain.pydantic_v1 import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langchain.chains.openai_functions import (
    create_openai_fn_chain,
    create_structured_output_chain,
)
from langchain.schema import AgentAction, AgentFinish
from langchain.chat_models import ChatOpenAI
from langchain.agents import tool, OpenAIFunctionsAgent, AgentExecutor
from langchain.schema import SystemMessage

try:
    os.environ["BING_SUBSCRIPTION_KEY"] = toml.load('.streamlit/secrets.toml')['llm_api_keys']['BING_SEARCH_API']
    os.environ['OPENAI_API_KEY'] = toml.load('.streamlit/secrets.toml')['llm_api_keys']['OPENAI_API_KEY']
    os.environ["BING_SEARCH_URL"] = "https://api.bing.microsoft.com/v7.0/search"
except:
    os.environ["BING_SUBSCRIPTION_KEY"] = toml.load('../.streamlit/secrets.toml')['llm_api_keys']['BING_SEARCH_API']
    os.environ['OPENAI_API_KEY'] = toml.load('../.streamlit/secrets.toml')['llm_api_keys']['OPENAI_API_KEY']
    os.environ["BING_SEARCH_URL"] = "https://api.bing.microsoft.com/v7.0/search"


class Question(BaseModel):
    question: str = Field(description="The trivia question")
    answer: str = Field(description="answer to the trivia question")
    category: str = Field(description="category of the question")
    difficulty: str = Field(description="difficulty of the question")  # options: easy, medium, hard


class QuestionSet(BaseModel):
    questions: List[Question] = Field(description="A list of questions for each category")


class FactCheckQuestion(BaseModel):
    question: str = Field(description="The trivia question")
    answer: str = Field(description="answer to the trivia question provided by the user")
    category: str = Field(description="category of the question provided by the user")
    fact_check: bool = Field(description="whether the answer is correct or not")
    explanation: str = Field(description="comment on the answer provided by the user")


def get_prompt(section, value):
    try:
        prompts = toml.load('prompts.toml')
    except:
        prompts = toml.load('../prompts.toml')
    return prompts[section][value]


def question_generator(categories: List[str], question_count: int = 10, difficulty: str = "Hard", context: str = None,
                       run_attempts=0, st_status=None) -> Dict[str, List[Dict[str, str]]]:
    """
    Uses an OpenAI model to generate a list of questions for each category.
    :param categories:
    :return:
    """
    llm = ChatOpenAI(temperature=0, model_name='gpt-4')
    if context:
        context = "Here are some questions and answers that the user would like to be asked. \n```\n" + context + "\n```"
    else:
        context = ""
    system_prompt = get_prompt('question_generation', 'system_prompt')
    human_prompt = get_prompt('question_generation', 'human_prompt')
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt),
    ]
    )
    llm_chain = LLMChain(llm=llm, prompt=prompt)
    try:
        st_status.update_status('Generating questions...') if st_status else None
        result = llm_chain.run(categories=categories, question_count=question_count, difficulty=difficulty,
                               context=context, verbose=True)
    except Exception as e:
        if run_attempts > 3:
            raise e
        else:
            return question_generator(categories=categories, question_count=question_count, difficulty=difficulty,
                                      run_attempts=run_attempts + 1)
    try:
        return eval(result)
    except:
        result = llm.predict(
            f"turn this into valid JSON so that your response can be parsed with python's `eval` function. {result}. This is a last resort, do NOT include any commentary or any warnings or anything else in this response. There should be no newlines or anything else. JUST the JSON.")
        return eval(result.split('```python')[1].split("```")[0].strip())


def fact_check_question(question, answer, category, try_attempts=0):
    """
    fact check a question, answer pair
    :param question:
    :param answer:
    :param category:
    :return:
    """
    search = BingSearchAPIWrapper(k=20)
    tools = [
        Tool(
            name="Search",
            func=search.run,
            description="useful for when you need to answer questions about current events. You should ask targeted questions",
        ),
    ]

    llm = ChatOpenAI(temperature=0, model_name='gpt-3.5-turbo-16k')
    system_message = SystemMessage(content=get_prompt('fact_checking', 'system_prompt'))
    prompt = OpenAIFunctionsAgent.create_prompt(system_message=system_message)
    agent = OpenAIFunctionsAgent(llm=llm, tools=tools, prompt=prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    human_prompt = get_prompt('fact_checking', 'human_prompt')
    human_prompt = human_prompt.format(question=question, answer=answer, category=category)
    parser = PydanticOutputParser(pydantic_object=FactCheckQuestion)
    try:
        # result = llm_chain.run(question=question, answer=answer, category=category)
        result = agent_executor.run(input=human_prompt, question=question, answer=answer, category=category,
                                    verbose=True)
        try:
            parsed_result = parser.parse(result)
        except Exception as e:
            print(e)
            result = result.split('}')[0] + '}'
            parsed_result = parser.parse(result)
    except Exception as e:
        if try_attempts > 6:
            raise e
        else:
            return fact_check_question(question, answer, category, try_attempts=try_attempts + 1)
    return parsed_result.dict()


def _fix_question(question, answer, category, explanation, previous_questions, run_attempts=0):
    """
    attempts to fix the question and answer pair
    :param question:
    :param answer:
    :param category:
    :param explanation:
    :param run_attempts:
    :return:
    """
    llm = ChatOpenAI(temperature=0, model_name='gpt-4')
    system_prompt = get_prompt('question_fixing', 'system_prompt')
    human_prompt = get_prompt('question_fixing', 'human_prompt')
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt),
    ]
    )
    llm_chain = LLMChain(llm=llm, prompt=prompt)
    try:
        result = llm_chain.run(question=question, answer=answer, category=category, explanation=explanation,
                               previous_questions=previous_questions, verbose=True)
    except Exception as e:
        if run_attempts > 5:
            raise e
        else:
            return _fix_question(question, answer, category, explanation, previous_questions,
                                 run_attempts=run_attempts + 1)
    try:
        return eval(result)
    except:
        result = llm.predict(
            f"turn this into valid JSON so that your response can be parsed with python's `eval` function. {result}. This is a last resort, do NOT include any commentary or any warnings or anything else in this response. There should be no newlines or anything else. JUST the JSON.")
        return eval(result.split('```python')[1].split("```")[0].strip())


def fix_question(question, answer, category, explanation, previous_questions, run_attempts=0):
    val = False
    k = 0
    while not val and k < 10:
        new_question = _fix_question(question, answer, category, explanation, previous_questions,
                                     run_attempts=run_attempts)
        # now
        new_fact_check = fact_check_question(new_question['question'], new_question['answer'], new_question['category'])
        val = new_fact_check['fact_check']
        question = new_fact_check['question']
        answer = new_fact_check['answer']
        category = new_fact_check['category']
        explanation = new_fact_check['explanation']
        k += 1

    return new_fact_check


def grade_responses(response_json):
    """
    grades the responses from the question generator
    :param response_json:
    :return:
    """
    final_score = pd.DataFrame(columns=['question', 'answer', 'category', 'user_answer', 'grade'])
    total_score = pd.DataFrame(
        columns=['category', 'total_questions', 'total_correct', 'total_incorrect', 'total_score'])
    st.write("Grading responses...")
    for key, val in eval(response_json).items():
        question, answer, category = key.split(' || ')
        user_answer = val['value']
        grade = _grade_answer(question, answer, user_answer)
        final_score.loc[len(final_score)] = [question, answer, category, user_answer, grade['grade']]

    for category in final_score.category.unique():
        category_score = final_score.loc[final_score.category == category]
        total_questions = len(category_score)
        total_correct = len(category_score.loc[category_score.grade == True])
        total_incorrect = len(category_score.loc[category_score.grade == False])
        total_score.loc[len(total_score)] = [category, total_questions, total_correct, total_incorrect,
                                             total_correct / total_questions]
    total_score.loc[len(total_score)] = ['total', len(final_score), len(final_score.loc[final_score.grade == True]),
                                         len(final_score.loc[final_score.grade == False]),
                                         len(final_score.loc[final_score.grade == True]) / len(final_score)]

    # make a table of the results
    st.balloons()
    st.table(total_score)
    st.table(final_score)
    return total_score, final_score


def _grade_answer(question, answer, user_answer, try_attempts=0):
    """
    the LLM checker that returns True if the answer is correct and False if its not
    :param question:
    :param answer:
    :param user_answer:
    :return:
    """
    llm = ChatOpenAI(temperature=0, model_name='gpt-4')
    system_prompt = get_prompt('answer_grading', 'system_prompt')
    human_prompt = get_prompt('answer_grading', 'human_prompt')
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", human_prompt),
    ]
    )
    grade_answer_schema = {
        "title": "Grade Answer Output",
        "description": "Result of grading the user's answer along with associated data.",
        "type": "object",
        "properties": {
            "question": {
                "title": "Question",
                "description": "The original question posed.",
                "type": "string"
            },
            "answer": {
                "title": "Correct Answer",
                "description": "The correct answer to the given question.",
                "type": "string"
            },
            "user_answer": {
                "title": "User's Answer",
                "description": "The answer provided by the user.",
                "type": "string"
            },
            "correct": {
                "title": "Correctness Status",
                "description": "Indicates if the user's answer is correct according to the rules in the system prompt.",
                "type": "boolean"
            }
        },
        "required": ["question", "answer", "user_answer", "correct"]
    }
    grade_answer_schema = {
        "title": "Grade Answer Output",
        "description": "Explanation of the grading result followed by the result itself.",
        "type": "object",
        "properties": {
            "explanation": {
                "title": "Explanation",
                "description": "A detailed explanation of why the user's answer is correct or incorrect.",
                "type": "string"
            },
            "grade": {
                "title": "Grade",
                "description": "Indicates if the user's answer is correct.",
                "type": "boolean"
            }
        },
        "required": ["explanation", "grade"]
    }
    llm_chain = create_structured_output_chain(output_schema=grade_answer_schema, llm=llm, prompt=prompt, verbose=True)
    # llm_chain = LLMChain(llm=llm, prompt=prompt)
    try:
        result = llm_chain.run(question=question, answer=answer, user_answer=user_answer, verbose=True)
        return result
    except Exception as e:
        if try_attempts > 3:
            print(f'failed to grade answer: {user_answer} with error: {e}')
            return {
                'correct': True}  # This cannot fail, so if it does, just return True
        return _grade_answer(question, answer, user_answer)
    # try:
    #     return eval(result)
    # except:
    #     try:
    #         result = llm.predict(
    #             f"turn this into valid JSON so that your response can be parsed with python's `eval` function. {result}. This is a last resort, do NOT include any commentary or any warnings or anything else in this response. There should be no newlines or anything else. JUST the JSON.")
    #         print(f'On the path to fail with result: {result}')
    #         return eval(result.split('```python')[1].split("```")[0].strip())
    #     except Exception as e:
    #         print(f'failed to grade answer 2: {user_answer} with error: {e}')
    #         return {'correct': True}


if __name__ == '__main__':
    categories = ['science', 'history', 'geography']
    result = question_generator(categories=categories)
    print(result)

    question = "Who discovered America?"
    answer = "Christopher Columbus"
    category = "geography"
    result = fact_check_question(question, answer, category)
    print(result)

    categories = ['science', 'history', 'geography']
    question_count = 10
    difficulty = 'Hard'
    context = pd.DataFrame(columns=['question', 'answer', 'category', 'difficulty'])
    context.loc[0] = ['Who discovered America?', 'Christopher Columbus', 'geography', 'Hard']
    context.loc[1] = ['Who was the first president of the United States?', 'George Washington', 'history', 'Hard']
    context.loc[2] = ['What is the capital of California?', 'Sacramento', 'geography', 'Hard']
    result = question_generator(categories=categories, question_count=question_count, difficulty=difficulty,
                                context=context.to_markdown())

    question = "Who is the current Prime Minister of the UK?"
    answer = "Boris Johnson"
    category = "news"
    explanation = "The current Prime Minister of the UK is Rishi Sunak, not Boris Johnson. Boris Johnson served as Prime Minister from 2019 to 2022."
    result = fix_question(question, answer, category, explanation)
    print(result)

    question = "Who is the current Prime Minister of the UK?"
    answer = "Boris Johnson"
    category = "news"
    explanation = "The current Prime Minister of the UK is not Boris Johnson."
    result = fix_question(question, answer, category, explanation,
                          previous_questions=['who is the current president of the US?'])
    print(result)