from functools import wraps
from flask import jsonify, request
from .models import Player, Game

def check_auth(username, password):
    return Player().check_password(username, password)

def authenticate():
    message = {'message': "Authentication Required"}
    resp = jsonify(message)

    resp.status_code = 401
    resp.headers['WWW-Authenticate'] = 'Basic realm="Example"'

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
		game = Game.query.filter_by(id=game_id)\
			   .filter((Game.hosting == player)|(Game.joining == player)).first()
		if not game:
			return authenticate()
		return f(*args, **kwargs)
	return decorated