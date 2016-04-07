from functools import wraps
from flask import jsonify, request
from .models import Player, Game, Meeple, Card

def check_auth(username, password):
    return Player().check_password(username, password)

def authenticate():
    message = {'message': "Authentication Required"}
    resp = jsonify(message)

    resp.status_code = 401
    resp.headers['WWW-Authenticate'] = 'Basic realm="Example"'

    return resp

def turn_auth():
	message = {'message': "It is not your turn"}
	resp = jsonify(message)

	resp.status_code = 422
	return resp

def meeple_auth():
	message = {'message': 'This is not your meeple'}
	resp = jsonify(message)

	resp.status_code = 422
	return resp

def card_auth():
	message = {'message':'This is not your card'}
	resp = jsonify(message)

	resp.status_code = 422
	return resp

def requires_auth(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		auth = request.authorization
		if not auth or not check_auth(auth.username, auth.password): 
			return authenticate()
		return f(*args, **kwargs)
	return decorated

def requires_game_auth(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		auth = request.authorization
		player = Player.query.filter_by(username = auth.username).first()
		game_id = kwargs['game_id']
		game = Game.query.filter_by(id=game_id).\
					filter((Game.hosting == player)|(Game.joining == player)).\
					first()
		if not game:
			return authenticate()
		return f(*args, **kwargs)
	return decorated

def requires_turn_auth(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		auth = request.authorization
		player = Player.query.filter_by(username = auth.username).first()
		game_id = kwargs['game_id']
		game = Game.query.filter_by(id=game_id).filter(Game.turn == player).first()
		if not game:
			return turn_auth()
		return f(*args, **kwargs)
	return decorated

def meeple_check(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		auth = request.authorization
		player = Player.query.filter_by(username = auth.username).first()
		game_id = kwargs['game_id']
		meeple_id = kwargs['meeple_id']
		meeple = Meeple.query.filter_by(game_id=game_id).filter_by(id=meeple_id).\
							  filter_by(player_id = player.id).first()
		if not meeple:
			return meeple_auth()
		return f(*args, **kwargs)
	return decorated

def card_check(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		auth = request.authorization
		player = Player.query.filter_by(username = auth.username).first()
		game_id = kwargs['game_id']
		card_id = kwargs['card_id']
		card = Card.query.filter_by(game_id=game_id).filter_by(id=card_id).\
						  filter_by(player_id = player.id).first()
		if not card:
			return card_auth()
		return f(*args, **kwargs)
	return decorated
