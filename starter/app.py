from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///songs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

@app.route('/')
def index():
    # TO DO  — ADD route and function for index


@app.route('/add', methods=['GET', 'POST'])
def add_post():
    # TO DO  - ADD route and function for adding a new post

if __name__ == '__main__':
    app.run(debug=True)
