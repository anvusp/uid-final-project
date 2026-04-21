from flask import Flask, render_template, request, redirect, url_for
import os
import json
from datetime import datetime
from enum import Enum

app = Flask(__name__)


class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    DRAG_AND_DROP = "drag_and_drop"


QUESTION_TYPES = {
    "MULTIPLE_CHOICE": QuestionType.MULTIPLE_CHOICE.value,
    "DRAG_AND_DROP": QuestionType.DRAG_AND_DROP.value,
}


def now_iso():
    return datetime.now().isoformat()


# ----------------------------
# Load content data
# ----------------------------
filename = os.path.join(app.static_folder, "data.json")
with open(filename, "r", encoding="utf-8") as data_file:
    data = json.load(data_file)

LESSONS = {lesson["id"]: lesson for lesson in data["lessons"]}
QUESTIONS = {question["id"]: question for question in data["questions"]}
TRANSITIONS = {transition["id"]: transition for transition in data["transitions"]}

LESSON_ORDER = data["lesson_order"]
QUIZ_ORDER = data["quiz_order"]


# ----------------------------
# Mock single-user backend state
# ----------------------------
USER_STATE = {
    "started": False,
    "started_at": None,
    "transition_views": [],
    "lesson_visits": [],
    "quiz_started_at": None,
    "quiz_completed_at": None,
    "quiz_answers": {},
    "event_log": [],
}


# ----------------------------
# State helpers
# ----------------------------
def reset_user_state():
    USER_STATE["started"] = True
    USER_STATE["started_at"] = now_iso()
    USER_STATE["transition_views"] = []
    USER_STATE["lesson_visits"] = []
    USER_STATE["quiz_started_at"] = None
    USER_STATE["quiz_completed_at"] = None
    USER_STATE["quiz_answers"] = {}
    USER_STATE["event_log"] = []


def log_event(event_type, payload):
    USER_STATE["event_log"].append(
        {
            "type": event_type,
            "payload": payload,
            "timestamp": now_iso(),
        }
    )


def record_transition_view(transition_id):
    USER_STATE["transition_views"].append(
        {
            "transition_id": transition_id,
            "viewed_at": now_iso(),
        }
    )
    log_event("transition_view", {"transition_id": transition_id})


def record_lesson_visit(lesson_id):
    USER_STATE["lesson_visits"].append(
        {
            "lesson_id": lesson_id,
            "entered_at": now_iso(),
        }
    )
    log_event("lesson_visit", {"lesson_id": lesson_id})


def record_quiz_start():
    if USER_STATE["quiz_started_at"] is None:
        USER_STATE["quiz_started_at"] = now_iso()
        log_event("quiz_started", {})


def record_quiz_complete():
    if USER_STATE["quiz_completed_at"] is None:
        USER_STATE["quiz_completed_at"] = now_iso()
        log_event("quiz_completed", {})


def record_quiz_answer(question_id, submission):
    USER_STATE["quiz_answers"][str(question_id)] = submission
    log_event(
        "quiz_answer",
        {
            "question_id": question_id,
            "submission": submission,
        },
    )


# ----------------------------
# Quiz helpers
# ----------------------------
def parse_question_type(question):
    return QuestionType(question["type"])


def extract_submission(question, request_obj):
    question_type = parse_question_type(question)

    if question_type == QuestionType.MULTIPLE_CHOICE:
        return request_obj.form.get("answer")

    if question_type == QuestionType.DRAG_AND_DROP:
        raw_mapping = request_obj.form.get("answer_map")
        if not raw_mapping:
            return {}

        try:
            return json.loads(raw_mapping)
        except json.JSONDecodeError:
            return {}

    raise ValueError(f"Unsupported question type: {question_type}")


def is_submission_correct(question, submission):
    question_type = parse_question_type(question)
    correct_answer = question.get("answer")

    if question_type == QuestionType.MULTIPLE_CHOICE:
        return submission == correct_answer

    if question_type == QuestionType.DRAG_AND_DROP:
        return submission == correct_answer

    raise ValueError(f"Unsupported question type: {question_type}")


def format_answer_for_display(answer):
    if isinstance(answer, dict):
        return json.dumps(answer, indent=2, sort_keys=True)
    if answer is None or answer == "":
        return "No answer submitted"
    return str(answer)


def calculate_score():
    correct = 0
    total = len(QUIZ_ORDER)

    for qid in QUIZ_ORDER:
        question = QUESTIONS[qid]
        submission = USER_STATE["quiz_answers"].get(str(qid))
        if is_submission_correct(question, submission):
            correct += 1

    return correct, total


def build_review_item(question, submission):
    question_type = parse_question_type(question)
    is_correct = is_submission_correct(question, submission)
    correct_answer = question.get("answer")

    item = {
        "id": question["id"],
        "title": question["title"],
        "is_correct": is_correct,
        "status_label": "Correct" if is_correct else "Incorrect",
        "status_class": "success" if is_correct else "danger",
        "show_question_type": False,
        "question_type_display": question_type.value,
        "show_user_answer": True,
        "user_answer_display": format_answer_for_display(submission),
        "show_correct_answer": True,
        "correct_answer_display": format_answer_for_display(correct_answer),
    }

    if question_type == QuestionType.MULTIPLE_CHOICE:
        return item

    if question_type == QuestionType.DRAG_AND_DROP:
        item["show_question_type"] = False
        item["show_correct_answer"] = False
        item["status_label"] = "Correct" if is_correct else "Needs review"
        item["status_class"] = "success" if is_correct else "warning"
        return item

    return item


def build_results_review():
    review = []

    for qid in QUIZ_ORDER:
        question = QUESTIONS[qid]
        submission = USER_STATE["quiz_answers"].get(str(qid))
        review.append(build_review_item(question, submission))

    return review


# ----------------------------
# Navigation helpers
# ----------------------------
def transition_target(transition_id):
    if transition_id == 1:
        return url_for("render_learnpage", id=LESSON_ORDER[0])
    if transition_id == 2:
        return url_for("render_learnpage", id=3)
    if transition_id == 3:
        return url_for("render_quizpage", id=QUIZ_ORDER[0])

    return url_for("render_homepage")


def get_lesson_prev_next(lesson_id):
    idx = LESSON_ORDER.index(lesson_id)

    if lesson_id == 1:
        prev_url = url_for("render_transitionpage", id=1)
    else:
        prev_lesson_id = LESSON_ORDER[idx - 1]
        if lesson_id == 3:
            prev_url = url_for("render_transitionpage", id=2)
        else:
            prev_url = url_for("render_learnpage", id=prev_lesson_id)

    if lesson_id == 2:
        next_url = url_for("render_transitionpage", id=2)
    elif lesson_id == 6:
        next_url = url_for("render_transitionpage", id=3)
    else:
        next_lesson_id = LESSON_ORDER[idx + 1]
        next_url = url_for("render_learnpage", id=next_lesson_id)

    return prev_url, next_url


def get_transition_prev_next(transition_id):
    if transition_id == 1:
        prev_url = None
        next_url = url_for("render_learnpage", id=LESSON_ORDER[0])
    elif transition_id == 2:
        prev_url = url_for("render_learnpage", id=2)
        next_url = url_for("render_learnpage", id=3)
    elif transition_id == 3:
        prev_url = url_for("render_learnpage", id=6)
        next_url = url_for("render_quizpage", id=QUIZ_ORDER[0])
    else:
        prev_url = url_for("render_homepage")
        next_url = url_for("render_homepage")

    return prev_url, next_url


def get_quiz_prev_next(question_id):
    idx = QUIZ_ORDER.index(question_id)

    if idx == 0:
        prev_url = url_for("render_transitionpage", id=3)
    else:
        prev_url = url_for("render_quizpage", id=QUIZ_ORDER[idx - 1])

    if idx == len(QUIZ_ORDER) - 1:
        next_url = url_for("render_results")
    else:
        next_url = url_for("render_quizpage", id=QUIZ_ORDER[idx + 1])

    return prev_url, next_url


# ----------------------------
# Routes
# ----------------------------
@app.route("/")
@app.route("/home")
def render_homepage():
    reset_user_state()
    log_event("start", {"message": "User started app"})
    return redirect(url_for("render_transitionpage", id=1))


@app.route("/transition/<int:id>")
def render_transitionpage(id):
    transition = TRANSITIONS.get(id)
    if not transition:
        return "Transition not found", 404

    record_transition_view(id)
    prev_url, next_url = get_transition_prev_next(id)

    return render_template(
        "transition.html",
        transition=transition,
        prev_url=prev_url,
        next_url=next_url,
        cta_url=transition_target(id),
    )


@app.route("/learn/<int:id>")
def render_learnpage(id):
    lesson = LESSONS.get(id)
    if not lesson:
        return "Lesson not found", 404

    record_lesson_visit(id)
    prev_url, next_url = get_lesson_prev_next(id)

    return render_template(
        "learn.html",
        lesson=lesson,
        prev_url=prev_url,
        next_url=next_url,
    )


@app.route("/quiz/<int:id>", methods=["GET", "POST"])
def render_quizpage(id):
    question = QUESTIONS.get(id)
    if not question:
        return "Question not found", 404

    parse_question_type(question)
    record_quiz_start()
    prev_url, next_url = get_quiz_prev_next(id)

    if request.method == "POST":
        submission = extract_submission(question, request)
        record_quiz_answer(id, submission)
        return redirect(next_url)

    return render_template(
        "quiz.html",
        question=question,
        prev_url=prev_url,
        next_url=next_url,
        QUESTION_TYPES=QUESTION_TYPES,
    )


@app.route("/results")
def render_results():
    record_quiz_complete()
    score, total = calculate_score()
    results_review = build_results_review()
    log_event("results_view", {"score": score, "total": total})

    return render_template(
        "quiz_results.html",
        score=score,
        total=total,
        results_review=results_review,
        user_state=USER_STATE,
    )


if __name__ == "__main__":
    app.run(debug=True)
