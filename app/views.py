import random
from . import app, db
from flask import Response, jsonify, request
from .models import Game, Card, BoardSpace, Player, Meeple, CardMovement
from .services import game as _game, player as _player, boardspace as _boardspace, \
	meeple as _meeple, card as _card
from .core import ParseException, ResponseError
from .schema import GameSchema, PlayerSchema, CardSchema, BoardSpaceSchema, MeepleSchema
from auth import requires_auth, requires_game_auth, requires_turn_auth, meeple_check, card_check

game_schema = GameSchema()
games_schema = GameSchema(many=True)
player_schema = PlayerSchema()
card_schema = CardSchema()
cards_schema = CardSchema(many=True)
boardspace_schema = BoardSpaceSchema()
boardspaces_schema = BoardSpaceSchema(many=True)
meeple_schema = MeepleSchema()
meeples_schema = MeepleSchema(many=True)

@app.route("/", methods=['GET'])
def hello():
	db.create_all()
	return "Created"

@app.route("/drop", methods=['GET'])
def drop():
	db.drop_all()
	return "Dropped	"

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
@requires_auth
def get_games():
	'''
	Returns a list of all games
	'''
	return _game.get_open_games()

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
	card = _card.draw(
		game_id,
		_player.get(username=request.authorization.username))
	end_turn(game_id)
	db.session.commit()
	return jsonify(card)

@app.route("/game/<int:game_id>/move/<int:meeple_id>", methods=['POST'])
@requires_auth
@requires_turn_auth 
@meeple_check
def move_meeple(game_id, meeple_id):
	try:
		result = _boardspace.move_meeple(
			request, 
			game_id,
			_meeple.get(game_id=game_id, id=meeple_id))
		end_turn(game_id)
		db.session.commit()
		return jsonify(result)
	except ResponseError as e:
		return jsonify(e.error)

@app.route("/game/<int:game_id>/hand/<int:card_id>", methods=['POST'])
@requires_auth
@requires_turn_auth 
@card_check
def play_card(game_id, card_id):
	try:
		player = _player.get(username=request.authorization.username)
		result = _boardspace.play_card(
			request,
			game_id,
			_meeple.all(game_id=game_id, player=player),
			_card.get(game_id=game_id, id=card_id))
		end_turn(game_id)
		db.session.commit()
		return jsonify(result)
	except ResponseError as e:
		return jsonify(e.error)

def get_movement(value):
	switcher = {
		'U': (0,1),
		'UR': (1,1),
		'DR': (1,0),
		'D':(0,-1),
		'DL':(-1,-1),
		'UL':(-1,0)
	}
	return switcher.get(value, "nothing")

def get_opposite_direction(value):
	switcher = {
		'U': 'D',
		'UR': 'DL',
		'DR': 'UL',
		'D':'U',
		'DL':'UR',
		'UL':'DR'
	}
	return switcher.get(value, "nothing")

def end_turn(game_id):
	"""Function that is called at the end of every turn

	The purpose of this function is to handle pieces moving after a completed turn
	The piece will be moves, rotated, and scored
	(Right now is very long, should probably be broken down)
	"""
	#Get all cards that have potential to move
	cards = Card.query.filter_by(game_id=game_id).\
			filter_by(value="P").\
			filter(Card.board_space_id != None).\
			all()
	print cards
	#Move all the cards
	for card in cards:
		x_y = get_movement(card.direction)
		new_space = BoardSpace.query.filter_by(game_id=game_id).\
			filter_by(x_loc = card.board_space.x_loc + x_y[0]).\
			filter_by(y_loc = card.board_space.y_loc + x_y[1]).\
			first()

		#if no space, flip in opposite direction
		if not new_space:
			card.direction = get_opposite_direction(card.direction)
		else:
			previous_space = card.board_space
			card.board_space = new_space

			#Check if card exists on current space, if no add points
			previous_card_movement = CardMovement.query.filter_by(board_space=previous_space).\
				filter_by(card = card).first()
			previous_card = Card.query.filter_by(board_space=previous_space).\
				filter(Card.value != "P").first()
			if not previous_card_movement and not previous_card:
				card.points = card.points + 1
				space = CardMovement(game_id = game_id, card = card, board_space=previous_space)
				db.session.add(space)

			#if current space, rotate
			current_space = Card.query.filter_by(game_id=game_id).\
				filter_by(board_space=new_space).filter(Card.value != "P").\
				filter(Card.id != card.id).first()
			if current_space:
				card.direction = current_space.value

			#Grab any meeples at current space, if they exist add points to score, then remove
			meeple = Meeple.query.filter_by(game_id=game_id).\
				filter_by(board_space=new_space).first()
			if meeple:
				game = Game.query.filter_by(id=game_id).first()
				if (game.hosting == meeple.player):
					game.hosting_score = card.points + game.hosting_score
				else:
					game.joining_score = card.points + game.joining_score
				card.board_space = None
				card.finished = True

	#End Turn 
	Game.change(game_id)