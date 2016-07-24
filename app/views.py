import random
from . import app, db
from flask import Response, jsonify, request
from .models import Game, Card, BoardSpace, Player, Meeple
from .services import game as _game, player as _player, boardspace as _boardspace, \
	meeple as _meeple, card as _card
from .core import ParseException, ResponseError
from auth import requires_auth, requires_game_auth, requires_turn_auth, meeple_check, card_check

@app.route("/player/", methods=['GET'])
@requires_auth
def get_player():
	return _player.get_response(username = request.authorization.username)

@app.route("/player/", methods=['POST'])
def create_player():
	try:
		return _player.create_request(request)
	except ParseException as e:
		return jsonify(e.error), e.code

@app.route("/player/generate", methods=['POST'])
def generate_player():
	player = _player.generate()
	return jsonify(player)

@app.route("/game", methods=['GET'])	
def get_games():
	'''
	Returns a list of all games
	'''
	response = _game.get_open_games()
	return jsonify(response)

@app.route("/game", methods=['POST'])
@requires_auth
def create_game():
	'''
	Create a new game
	'''
	result = _game.create_game(
		request,
		_player.get(username=request.authorization.username))
	return result

@app.route("/game/<int:game_id>", methods=['GET'])
@requires_auth
@requires_game_auth
def get_game(game_id):
	'''
	Get information on game
	'''
	return _game.get_response(id=game_id)

@app.route("/game/<int:game_id>", methods=['POST'])
@requires_auth
def join_game(game_id):
	'''
	Join the game_id
	'''
	return _game.join_game(
		_game.get(id=game_id),
		_player.get(username=request.authorization.username))

@app.route("/game/<int:game_id>/hand", methods=["GET"])
@requires_auth
@requires_game_auth
def get_hand(game_id):
	player = _player.get(username=request.authorization.username)
	cards = _card.all_response(game_id=game_id,player=player)
	return cards

@app.route("/game/<int:game_id>/meeples", methods=["GET"])
@requires_auth
@requires_game_auth
def get_meeples(game_id):
	player = _player.get(username=request.authorization.username)
	meeples = _meeple.all_response(game_id=game_id,player=player)
	return meeples

@app.route("/game/<int:game_id>/draw", methods=['GET'])
@requires_auth
@requires_turn_auth
def draw_card(game_id):
	card = _game.turn.draw_card(request, game_id)
	return jsonify(card)

@app.route("/game/<int:game_id>/move/<int:meeple_id>", methods=['POST'])
@requires_auth
@requires_turn_auth 
@meeple_check
def move_meeple(game_id, meeple_id):
	result = _game.turn.move_meeple(request, game_id, meeple_id)
	return _game.get_response(id=game_id)

@app.route("/game/<int:game_id>/hand/<int:card_id>", methods=['POST'])
@requires_auth
@requires_turn_auth 
@card_check
def play_card(game_id, card_id):
	result = _game.turn.play_card(request, game_id, card_id)
	return _game.get_response(id=game_id)

@app.route("/game/<int:game_id>/spot/<int:x>/<int:y>")
def get_space(game_id, x, y):
	result = _boardspace.get_response(game_id=game_id,x_loc=x,y_loc=y)
	return result