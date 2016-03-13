from flask.ext.sqlalchemy import sqlalchemy
from sqlalchemy.exc import IntegrityError
from . import db

class Player(db.Model):
	__tablename__ = 'player'
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	username = db.Column(db.String(200), unique=True)
	password = db.Column(db.String(200))
	auth_token = db.Column(db.String(200))
	player1 = db.relationship("Game", backref='hosting', lazy='dynamic', foreign_keys='Game.player1')
	player2 = db.relationship("Game", backref='joining', lazy='dynamic', foreign_keys='Game.player2')

	def new_player(self):
		try:
			db.session.add(self)
			db.session.commit()
		except IntegrityError:
			return dict(error = "This username already exists")

	def check_password(self, username, password):
		result = self.query.filter_by(username = username).filter_by(password = password).first()
		if result:
			return True
		return False;

class Game(db.Model):
	__tablename__ = 'game'
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	status = db.Column(db.String(200))
	player1 = db.Column(db.Integer, db.ForeignKey('player.id'))
	player2 = db.Column(db.Integer, db.ForeignKey('player.id'))
	deck = db.relationship("Card", backref='game', lazy='dynamic')
	board = db.relationship("BoardSpace", backref='game', lazy='dynamic')

class Card(db.Model):
	__tablename__ = 'card'
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	value = db.Column(db.String(200))
	position = db.Column(db.Integer)
	game_id = db.Column(db.Integer, db.ForeignKey('game.id'))

class BoardSpace(db.Model):
	__tablename__ = 'board_space'
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	x_loc = db.Column(db.Integer)
	y_loc = db.Column(db.Integer)
	game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
	card_id = db.Column(db.Integer, db.ForeignKey('card.id'))

class Meeple(db.Model):
	__tablename__ = 'meeple'
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
	player_id = db.Column(db.Integer, db.ForeignKey('player.id'))