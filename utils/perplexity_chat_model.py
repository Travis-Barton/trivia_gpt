import json
from langsmith.run_trees import RunTree
from openai import OpenAI
import toml
import os
from datetime import datetime

print(os.getcwd())
secrets = toml.load(".streamlit/secrets.toml")
os.environ['LANGCHAIN_PROJECT'] = secrets["langsmith_api"]["langsmith_project"]
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = secrets["langsmith_api"]["langsmith_api"]
PERPLEXITY_API_KEY = secrets["perplexity_api"]["PERPLEXITY_API_KEY"]


def get_prompt(section, value):
    try:
        prompts = toml.load('prompts.toml')
    except:
        prompts = toml.load('../prompts.toml')
    return prompts[section][value]


class FactChecker:
    def __init__(self, question, answer, category):
        self.question = question
        self.answer = answer
        self.category = category

    def check_fact(self):

        messages = [
            {
              "role": "system",
              "content": (
                  f"Current date: {datetime.now()} "
                  "You are an artificial intelligence fact checker and you are responsible "
                  "for fact checking an answer to a question. Respond with whether the answer is correct,"
                  "or incorrect, and provide a brief explanation as to your reasoning."
              ),
            },
            {
                "role": "user",
                "content": (
                    "The question is: " + self.question + " "
                    "The answer is: " + self.answer + " "
                    "Respond using a JSON format with the following fields: "
                    "fact_check (boolean), explanation (string)"
                ),
            },
          ]
        # messages = [
        #     {
        #         "role": "system",
        #         "content": get_prompt("fact_checking", "system_prompt")
        #     },
        #     {
        #         "role": "user",
        #         "content": get_prompt("fact_checking", "human_prompt").format(
        #                                                            question=self.question,
        #                                                            answer=self.answer,
        #                                                            category=self.category
        #         )
        #     }
        # ]
        # extra_text = """Remember, always respond in JSON with the format:
        # {
        #     "category": "category",
        #     "question": "question",
        #     "answer": "answer",
        #     "fact_check": Boolean,
        #     "explanation": "explanation as to WHY the answer is correct or incorrect",
        # }"""
        # messages[1]["content"] = messages[1]["content"] + extra_text
        rt = RunTree(
            run_type="llm",
            name="Perplexity Call RunTree",
            inputs={
                "messages": messages},
            tags=["Perplexity Fact-check"],
        )

        client = OpenAI(api_key=PERPLEXITY_API_KEY, base_url="https://api.perplexity.ai")
        response = client.chat.completions.create(
              model="pplx-70b-online",
              messages=messages,
          )
        print(response.choices[0].message.content)
        rt.end(outputs={'output': response.choices[0].message.content})
        rt.post()
        if response.choices[0].message.content:
            return response.choices[0].message.content
        else:
            return "I'm sorry, I cannot answer that question at the moment."


if __name__ == "__main__":
    question = "What is the capital of France?"
    answer = "Paris"
    fact_check = FactChecker(question, answer, "Geography")
    print(fact_check.check_fact())
