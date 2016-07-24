from flask import Flask, g
from flask.ext.sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin
from sqlite3 import dbapi2 as sqlite3

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
#app.config['SQLALCHEMY_ECHO'] = True
app.debug = True
CORS(app)
db = SQLAlchemy(app)

def init_db():
    """Initializes the database."""
    db.create_all()

from . import views