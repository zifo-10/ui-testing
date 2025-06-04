import uuid
from copy import copy


def process_answers(answers, correct_id, new_correct_id, question_id):
    for ans in answers:
        ans.answer_id = new_correct_id if ans.answer_id == correct_id else str(uuid.uuid4())
        ans.question_id = question_id
    return answers

def process_alternatives(alternatives):
    for alt in alternatives:
        alt.question_id = str(uuid.uuid4())
        old_correct_id = copy(alt.correct_answer_id)
        new_correct_id = str(uuid.uuid4())
        alt.correct_answer_id = new_correct_id
        alt.answer = process_answers(alt.answer, old_correct_id, new_correct_id, alt.question_id)
    return alternatives

def process_quiz_questions(quiz, paragraph_id):
    quiz_with_paragraph_id = []
    for q in quiz:
        q.question_id = str(uuid.uuid4())

        # Update correct answer
        old_correct_id = copy(q.correct_answer_id)
        new_correct_id = str(uuid.uuid4())
        q.correct_answer_id = new_correct_id

        # Assign question_id to skills
        for skill in q.question_skills_and_objective:
            skill.question_id = q.question_id

        # Process answers
        q.answer = process_answers(q.answer, old_correct_id, new_correct_id, q.question_id)

        # Process alternatives
        q.alternative_questions = process_alternatives(q.alternative_questions)

        dumped = q.model_dump()
        dumped["paragraph_id"] = paragraph_id
        quiz_with_paragraph_id.append(dumped)
    return quiz_with_paragraph_id
