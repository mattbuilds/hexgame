from flask.ext.sqlalchemy import sqlalchemy
from sqlalchemy.exc import IntegrityError
from . import db

class Player(db.Model):
	__tablename__ = 'player'
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	username = db.Column(db.String(200), unique=True)
	password = db.Column(db.String(200))
	auth_token = db.Column(db.String(200))
	hosting = db.relationship("Game", backref='hosting', lazy='dynamic', foreign_keys='Game.hosting_id')
	joining = db.relationship("Game", backref='joining', lazy='dynamic', foreign_keys='Game.joining_id')
	turn = db.relationship("Game", backref='turn', lazy='dynamic', foreign_keys='Game.turn_id')
	card = db.relationship("Card", backref='player', lazy='dynamic')
	meeple = db.relationship("Meeple", backref='player', lazy='dynamic')

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
	hosting_id = db.Column(db.Integer, db.ForeignKey('player.id'))
	hosting_score = db.Column(db.Integer, default=0)
	joining_id = db.Column(db.Integer, db.ForeignKey('player.id'))
	joining_score = db.Column(db.Integer, default=0)
	turn_id = db.Column(db.Integer, db.ForeignKey('player.id'))
	deck = db.relationship("Card", backref='game', lazy='dynamic')
	board = db.relationship("BoardSpace", backref='game', lazy='dynamic')
	bot_deck = db.relationship("BotCard", backref='game', lazy='dynamic')
	meeple = db.relationship("Meeple", backref='game', lazy='dynamic')
	card_movement = db.relationship("CardMovement", backref='game', lazy='dynamic')

	@classmethod
	def change(cls, game_id):
		result = Game.query.filter_by(id=game_id).first()
		if result.turn == result.hosting:
			result.turn = result.joining
		else:
			result.turn = result.hosting

class Bot(db.Model):
	__tablename__ = 'bot'
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
	board_space = db.relationship("BoardSpace", backref='bot', lazy='dynamic')

class BotCard(db.Model):
	__tablename__ = 'bot_card'
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	value = db.Column(db.String(200))
	game_id = db.Column(db.Integer, db.ForeignKey('game.id'))

class BoardSpace(db.Model):
	__tablename__ = 'board_space'
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	x_loc = db.Column(db.Integer)
	y_loc = db.Column(db.Integer)
	game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
	bot_id = db.Column(db.Integer, db.ForeignKey('bot.id'))
	meeple = db.relationship("Meeple", uselist=False, backref='board_space')
	card = db.relationship("Card", uselist=False, backref='board_space')
	movement = db.relationship("CardMovement", backref="board_space")

	@classmethod
	def get(self,x,y,game):
		space = BoardSpace.query.filter_by(x_loc = x).filter_by(y_loc = y).\
								  filter_by(game=game).first()
		return space

class Card(db.Model):
	__tablename__ = 'card'
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	value = db.Column(db.String(200))
	direction = db.Column(db.String(200))
	color = db.Column(db.Integer)
	points = db.Column(db.Integer)
	position = db.Column(db.Integer)
	finished = db.Column(db.Boolean, default=False, nullable=False)
	movement = db.relationship("CardMovement", backref="card", lazy="dynamic")
	player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
	game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
	board_space_id = db.Column(db.Integer, db.ForeignKey('board_space.id'))

class CardMovement(db.Model):
	__tablename__ = 'card_movement'
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
	card_id = db.Column(db.Integer, db.ForeignKey('card.id'))
	board_space_id = db.Column(db.Integer, db.ForeignKey('board_space.id'))

class Meeple(db.Model):
	__tablename__ = 'meeple'
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
	player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
	board_space_id = db.Column(db.Integer, db.ForeignKey('board_space.id'))

	@classmethod
	def add_meeple(self, game, player, space):
		a = Meeple(game=game, player=player, board_space=space)
		db.session.add(a)