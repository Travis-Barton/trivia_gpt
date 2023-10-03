import datetime
from abc import ABC
import pandas as pd
from utils.firebase_tools import get_db


class Question:
    question: str
    answer: str
    category: str
    game_id: str
    question_id: str
    revealed: bool
    created_at: datetime.datetime
    modified_at: datetime.datetime
    correct: bool
    order: int

    def __init__(self, question, answer, category, game_id, question_id, revealed, created_at, modified_at,
                 order):
        self.question = question
        self.answer = answer
        self.category = category
        self.game_id = game_id
        self.question_id = question_id
        self.revealed = revealed
        self.created_at = created_at
        self.modified_at = modified_at
        self.order = order

    @staticmethod
    def load(question_id):
        """
        Loading firestore object from firestore db
        :param question_id:
        :return:
        """
        question_ref = get_db().collection(u'questions').document(question_id)
        question = question_ref.get().to_dict()
        return Question(
            question=question['question'],
            answer=question['answer'],
            category=question['category'],
            game_id=question['game_id'],
            question_id=question['question_id'],
            revealed=question['revealed'],
            created_at=question['created_at'],
            modified_at=question['modified_at'],
            order=question['order'],
        )

    def write(self):
        """
        Writes the current state to fb
        :return:
        """
        question_ref = get_db().collection(u'questions').document(self.question_id)
        question_ref.update({
            'question': self.question,
            'answer': self.answer,
            'category': self.category,
            'game_id': self.game_id,
            'question_id': self.question_id,
            'revealed': self.revealed,
            'created_at': self.created_at,
            'modified_at': self.modified_at,
            'correct': self.correct,
            'order': self.order,
        })


class Answer:
    answer: str
    game_id: str
    question_id: str
    timestamp: datetime.datetime
    graded: bool
    user_id: str

    def __init__(self, answer, game_id, question_id, timestamp, graded, user_id):
        self.answer = answer
        self.game_id = game_id
        self.question_id = question_id
        self.timestamp = timestamp
        self.graded = graded
        self.user_id = user_id

    @staticmethod
    def load(question_id):
        """
        Loading firestore object from firestore db
        :param question_id:
        :return:
        """
        answer_ref = get_db().collection(u'answers').document(question_id)
        answer = answer_ref.get().to_dict()
        return Answer(
            answer=answer['answer'],
            game_id=answer['game_id'],
            question_id=answer['question_id'],
            timestamp=answer['timestamp'],
            graded=answer['graded'],
            user_id=answer['user_id'],
        )

    def write(self):
        """
        Writes the current state to fb
        :return:
        """
        answer_ref = get_db().collection(u'answers').document(self.question_id)
        answer_ref.update({
            'answer': self.answer,
            'game_id': self.game_id,
            'question_id': self.question_id,
            'timestamp': self.timestamp,
            'graded': self.graded,
            'user_id': self.user_id,
        })


class Game:
    game_id: str
    user_ids: list[str]
    question_ids: list[str]
    show_answers: bool
    def __init__(self, game_id, user_ids, question_ids, show_answers):
        self.game_id = game_id
        self.user_ids = user_ids
        self.question_ids = question_ids
        self.show_answers = show_answers

    @staticmethod
    def load(question_id):
        """
        Loading firestore object from firestore db
        :param question_id:
        :return:
        """
        game_ref = get_db().collection(u'games').document(question_id)
        game = game_ref.get().to_dict()
        return Game(
            game_id=game['game_id'],
            user_ids=game['user_ids'],
            question_ids=game['question_ids'],
            show_answers=game['show_answers'],
        )

    def write(self):
        """
        Writes the current state to fb
        :return:
        """
        game_ref = get_db().collection(u'games').document(self.game_id)
        game_ref.update({
            'game_id': self.game_id,
            'user_ids': self.user_ids,
            'question_ids': self.question_ids,
            'show_answers': self.show_answers,
        })

    @staticmethod
    def get_user_scores(game_id):
        """
        returns a dict of user scores structured like this:
        {
            user_id: int,
            user_id: int,
            ...
        }
        :param game_id:
        :return:
        """
        answers_ref = get_db().collection(u'answers').where(u'game_id', u'==', game_id).stream()
        answers = {doc.id: doc.to_dict() for doc in answers_ref}
        scores = {}
        for answer_id, answer in answers.items():
            if answer['user_id'] not in scores:
                scores[answer['user_id']] = 0
            if answer['correct']:
                scores[answer['user_id']] += 1
        return scores

    @staticmethod
    def check_all_answers_graded(game_id) -> bool:
        """
        Returns true if all answers are graded
        :param game_id:
        :return:
        """
        answers_ref = get_db().collection(u'answers').where(u'game_id', u'==', game_id).where(u'graded', u'==', False).stream()
        answers = {doc.id: doc.to_dict() for doc in answers_ref}
        return len(answers) == 0

    @staticmethod
    def get_scoreboard(game_id) -> pd.DataFrame:
        """
        Returns a dataframe of the scoreboard with the index as the question_id and columns as the team names
        :param game_id:
        :return:
        """
        answers_ref = get_db().collection(u'answers').where(u'game_id', u'==', game_id).stream()
        questions_ref = get_db().collection(u'questions').where(u'game_id', u'==', game_id).stream()
        questions = {doc.id: doc.to_dict() for doc in questions_ref}
        answers = {doc.id: doc.to_dict() for doc in answers_ref}
        scores = {}
        team_names = list(set([ans['user_id'] for ans in answers.values()]))
        questions_list = list(set([ques['question'] for ques in questions.values()]))
        data = pd.DataFrame(index=questions_list, columns=team_names)
        data.fillna(False, inplace=True)
        for answer_id, answer in answers.items():
            question_text = questions[answer['question_id']]['question']
            data.loc[question_text, answer['user_id']] = answer['correct']
        return data

    @staticmethod
    def get_leaderboard(game_id) -> pd.DataFrame:
        """
        this returns a pandas df of the points each user has sorted descending
        :param game_id:
        :return:
        """
        scores = Game.get_user_scores(game_id)
        scores_df = pd.DataFrame.from_dict(scores, orient='index', columns=['score'])
        scores_df.sort_values(by=['score'], ascending=False, inplace=True)
        return scores_df

    @staticmethod
    def get_user_answers(game_id):
        """
        returns a dict of user answers structured like this:
        {
            user_id: {
                question_id: answer,
                question_id: answer,
                ...
            },
            user_id: {
                question_id: answer,
                question_id: answer,
                ...
            },
            ...
        }
        :param game_id:
        :return:
        """
        answers_ref = get_db().collection(u'answers').where(u'game_id', u'==', game_id).stream()
        user_answers = {}
        for doc in answers_ref:
            answer = doc.to_dict()
            user_id = answer['user_id']
            question_id = answer['question_id']
            question = Question.load(question_id)

            if user_id not in user_answers:
                user_answers[user_id] = {}

            user_answers[user_id][question.question] = answer['answer']

        return user_answers


