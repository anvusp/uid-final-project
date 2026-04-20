from flask import Flask, render_template, json
import os
app = Flask(__name__)

# Load Data
filename = os.path.join(app.static_folder, 'data.json')
with open(filename) as data_file:
  data = json.load(data_file)
LESSONS = {lesson["id"]: lesson for lesson in data["lessons"]}
QUESTIONS = {question["id"]: question for question in data["questions"]}
TRANSITIONS = {transition["id"]: transition for transition in data["transitions"]}
TIMELINE = data["timeline"]


# Route 1: Home Page -------------------------------------------------------
@app.route('/')
def render_homepage():
  return render_template('transition.html', transition = TRANSITIONS[1])

# Route 2: Learn Page -------------------------------------------------------
@app.route('/learn/<int:id>')
def render_learnpage(id=None):
  lesson = LESSONS.get(id)
  if not lesson: 
    return "Lesson not found", 404
  
  return render_template('learn.html', lesson=lesson)

# Route 3: Quiz Page -------------------------------------------------------
@app.route('/quiz/<int:id>')
def render_quizpage(id=None):
  question = QUESTIONS.get(id)
  if not question: 
    return "Question not found", 404
  
  return render_template('quiz.html', question=question)

# Route 4: Transition Pages -------------------------------------------------------
@app.route('/transition/<int:id>')
def render_transitionpage(id=None):
  transition = TRANSITIONS.get(id)
  if not transition:
    return "Transition not found", 404

  return render_template('transition.html', transition=transition)

# Route 5: Quiz Results Page -------------------------------------------------------
@app.route('/results')
def render_results():
  return render_template('quiz_results.html')