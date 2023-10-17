import logging

import firebase_admin
from utils.language_model_tools import _grade_answer
from utils.firebase_tools import get_db
from models.componants import Question, Answer
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
    })
    print(f'Question {question_id} graded {grade["grade"]} with {user_answer} for reason {grade["explanation"]}')
    return {'message': f'graded {question_id} for {user_answer}'}

