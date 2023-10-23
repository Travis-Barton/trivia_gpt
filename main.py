import logging
from firebase_admin import credentials, firestore

import firebase_admin
from utils.language_model_tools import _grade_answer
from utils.firebase_tools import get_db
from models.componants import Question, Answer, Game
import datetime
# reaction to firestore change in "answer"


def grade_question(data, context):
    """
    This listens to the "answers" document write in firestore and uses the "_grade_answer" endpoint.

    :param data:
    :param context:
    :return:

    upload command:
    ```
    gcloud functions deploy grade_question \
        --runtime python310 \
        --entry-point grade_question \
        --allow-unauthenticated \
        --timeout 540s \
        --memory 1GB \
        --trigger-event providers/cloud.firestore/eventTypes/document.write \
        --trigger-resource "projects/trivia-gpt-backend/databases/(default)/documents/answers/{document}" \
        --ignore-file=.gcloudignore
    ```
    """
    # if already graded, do nothing
    if data['value']['fields']['graded']['booleanValue']:
        return {'message': 'already graded'}
    print(f'grading {context.resource}')
    document_id = context.resource.split('/answers/')[1].split('/')[0]
    print(f'grading {document_id}')
    question_id = data["value"]["fields"]["question_id"]["stringValue"]
    user_answer = data['value']['fields']['answer']['stringValue']
    question = Question.load(question_id)
    grade = _grade_answer(question=question.question, answer=question.answer, user_answer=user_answer)
    print(f'graded {question_id}: {question.question} with {user_answer} as {grade["grade"]}')
    db = get_db()
    db.collection(u'answers').document(document_id).update({
        'correct': grade['grade'],
        'graded': True,
        'reason': grade['explanation'],
    })
    print(f'Question {question_id} graded {grade["grade"]} with {user_answer} for reason {grade["explanation"]}')
    return {'message': f'graded {question_id} for {user_answer}'}


# every time an answer is submitted there should be a function that listens for that and updates a game_score attr
# in the game document. That way we can take the computation off of the streamlit app and make it a backend thing.
    # reaction to firestore change in "answer"

def update_scoreboard(data, context):
    """
    NOT CURRENTLY IN USE BUT SOMEDAY WILL BE
        cloud functions like these will be how we make a streamlit app run fast an efficient.
    :param data:
    :param context:
    :return:

    upload command:
    ```
    gcloud functions deploy update_scoreboard \
        --runtime python310 \
        --entry-point update_scoreboard \
        --allow-unauthenticated \
        --timeout 540s \
        --memory 1GB \
        --trigger-event providers/cloud.firestore/eventTypes/document.write \
        --trigger-resource "projects/trivia-gpt-backend/databases/(default)/documents/answers/{document}" \
        --ignore-file=.gcloudignore
    ```
    """

    # find the total score for that user in that game
    # update the game document with that score

    # if not graded, do nothing
    if not data['value']['fields']['graded']['booleanValue']:
        return {'message': 'not graded'}
    print(f'updating scoreboard for {context.resource}')
    document_id = context.resource.split('/answers/')[1].split('/')[0]
    print(f'updating scoreboard for {document_id}')
    game_id = data["value"]["fields"]["game_id"]["stringValue"]
    user_id = data["value"]["fields"]["user_id"]["stringValue"]
    game = Game.load(game_id)
    scores = game.get_user_scores(game.game_id)
    score = scores[user_id]
    print(f'updating scoreboard for {game_id}: {user_id} with {score}')
    db = get_db()
    db.collection(u'games').document(game_id).update({
        'scores': firestore.ArrayUnion([{user_id: score}])
    })
    print(f'updated scoreboard for {game_id}: {user_id} with {score}')
