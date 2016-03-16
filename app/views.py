import random
from . import app, db
from flask import Response, jsonify, request
from .models import Game, Card, BoardSpace, Player
from auth import requires_auth
from marshmallow import Schema, fields, post_load

class PlayerSchema(Schema):
	id = fields.Int()
	username = fields.Str()
	password = fields.Str(load_only=True)

	@post_load
	def make_player(self, data):
		return Player(**data)

class GameSchema(Schema):
	id = fields.Int(dump_only=True)
	status = fields.Str()
	deck = fields.Nested('CardSchema', many=True, exclude=('game',))
	board = fields.Nested('BoardSpaceSchema',many=True, exclude=('game,'))
	hosting = fields.Nested(PlayerSchema, only=["id", "username"])
	joining = fields.Nested(PlayerSchema, only=["id", "username"])
	turn = fields.Nested(PlayerSchema, only=["id", "username"])

	@post_load
	def make_game(self, data):
		return Game(**data)

	def game_info(self, data):
		result = self.dump(data)
		try:
			del result.data['deck']
		except:
			for x in result.data:
				del x['deck']
		return result

class CardSchema(Schema):
	value = fields.Str()
	position = fields.Int()
	game = fields.Nested(GameSchema, only=["id"])

	@post_load
	def make_card(self, data):
		return Card(**data)

class BoardSpaceSchema(Schema):
	x_loc = fields.Int()
	y_loc = fields.Int()
	card = fields.Nested(CardSchema, only=["value"])
	game = fields.Nested(GameSchema, only=["id"])

	@post_load
	def make_boardspace(self, data):
		return BoardSpace(**data)

game_schema = GameSchema()
games_schema = GameSchema(many=True)
player_schema = PlayerSchema()
card_schema = CardSchema()
boardspace_schema = BoardSpaceSchema()
boardspaces_schema = BoardSpaceSchema(many=True)

def create_deck(game):
	card_types = ['UL','U', 'UR', 'DR', 'D', 'DL']
	deck = []
	print game
	for x in xrange(0,36):
		value = x % 6
		card = dict(position = x, value=card_types[value], game=game)
		result = Card(**card)
		db.session.add(result)
	db.session.commit()

	# Kind of hacky, can be made better by calling all the cards in a game at once,
	# update in objects, then commit to the database
	for x in range(0,36):
		switch = random.randint(0,35)
		card1 = Card.query.filter_by(position=x).filter_by(game=game).first()
		card2 = Card.query.filter_by(position=switch).filter_by(game=game).first()
		card1.position = switch
		card2.position = x
		db.session.commit()

def create_board(game):
	for x in xrange(-6,7):
		for y in xrange(-5,6):
			if abs(y-x) < 6:
				space = BoardSpace(x_loc = x, y_loc = y, game=game)
				db.session.add(space)

@app.route("/", methods=['GET'])
def hello():
	db.create_all()
	return "Created"

@app.route("/player", methods=['GET'])
@requires_auth
def get_player():
	player = Player.query.filter_by(username=request.authorization.username).first()
	result = player_schema.dump(player)
	return jsonify(result.data)

@app.route("/player", methods=['POST'])
def create_player():
	json = request.get_json()
	data,errors = player_schema.load(json)
	if errors:
		return jsonify(errors), 422
	print data
	player = player_schema.make_player(json)
	errors = player.new_player()
	if errors:
		return jsonify(errors), 422
	result = player_schema.dump(player)
	return jsonify(result.data)

@app.route("/game", methods=['GET'])
@requires_auth
def get_games():
	'''
	Returns a list of all games
	'''
	games = Game.query.all()
	result = games_schema.game_info(games)
	return jsonify({"games":result.data})

@app.route("/game", methods=['POST'])
@requires_auth
def create_game():
	'''
	Create a new game
	'''
	json_data = request.get_json()
	data, errors = game_schema.load(json_data)
	if errors:
		return jsonify(errors), 422
	data.hosting = Player.query.filter_by(username=request.authorization.username).first()
	db.session.add(data)
	create_deck(data)
	create_board(data)
	db.session.commit()
	result = game_schema.game_info(data)
	return jsonify({'result':result.data})

@app.route("/game/<int:game_id>", methods=['GET'])
@requires_auth
def get_game(game_id):
	'''
	Get information on game
	'''
	game = Game.query.filter_by(id=game_id).first()
	print game.deck
	result = game_schema.game_info(game)
	return jsonify(result.data)

@app.route("/game/<int:game_id>", methods=['POST'])
@requires_auth
def join_game(game_id):
	'''
	Join the game_id
	'''
	game = Game.query.filter_by(id=game_id).first()
	if game.joining:
		return "Already Full"
	player = Player.query.filter_by(username=request.authorization.username).first()
	if game.hosting  == player:
		return "Cannot Join your own game"
	game.joining = player
	game.status = "In Progress"
	game.turn = game.hosting
	db.session.commit()
	return 'Join %d' % game_id

@app.route("/game/<int:game_id>/deal", methods=['GET'])
def deal_hand(game_id):
	return 'Get %d' % game_id

@app.route("/game/<int:game_id>/draw/<int:meeple_id>", methods=['POST'])
def draw_card(game_id, meeple_id):
	return 'Post %d' % game_id

@app.route("/game/<int:game_id>/move/<int:meeple_id>", methods=['POST'])
def move_meeple(game_id, meeple_id):
	return 'Post %d %d' % (game_id, meeple_id)

@app.route("/game/<int:game_id>/play/<int:meeple_id>", methods=['POST'])
def play_card(game_id, meeple_id):
	return 'Post %d %d' % (game_id, meeple_id)

@app.route("/game/<int:game_id>/submit", methods=['POST'])
def submit_turn(game_id):
	return 'Post %d' % game_id