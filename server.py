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
  return render_template('homepage.html', lesson = LESSONS[1])

# Route 1: Learn Page -------------------------------------------------------
@app.route('/learn/<int:id>')
def render_learnpage(id=None):
  lesson = LESSONS.get(id)
  if not lesson: 
    return "Lesson not found", 404
  
  return render_template('learn.html', lesson=lesson)

# Route 2: Quiz Page 
@app.route('/quiz/<int:id>')
def render_quizpage(id=None):
  question = QUESTIONS.get(id)
  if not question: 
    return "Question not found", 404
  
  return render_template('quiz.html', question=question)