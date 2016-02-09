from flask import Flask, request, render_template


app = Flask(__name__)
app.debug = True

data = None

@app.route('/')
def index():

