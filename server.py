from flask import Flask, render_template
app = Flask(__name__)

# Route 1: Home Page -------------------------------------------------------
@app.route('/')
def render_homepage():
  return render_template('homepage.html')

# Route 1: Learn Page -------------------------------------------------------
@app.route('/learn')
def render_learnpage():
  return render_template('learn.html')