import random
from . import app, db
from flask import Response, jsonify, request
from .models import Game, Card, BoardSpace, Player, Meeple, CardMovement
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

def create_deck(game):
	card_types = ['UL','U', 'UR', 'DR', 'D', 'DL']
	deck = []
	print game
	for x in xrange(0,36):
		value = x % 6
		card = dict(position = x, value=card_types[value], game=game)
		result = Card(**card)
		db.session.add(result)

	color = ['']
	for x in xrange(0,6):
		direction = x % 6
		card = dict(position = 36+ x, value = 'P', direction = card_types[direction],
					game=game, color=x, points=0)
		result = Card(**card)
		db.session.add(result)

	db.session.commit()

	# Kind of hacky, can be made better by calling all the cards in a game at once,
	# update in objects, then commit to the database
	for x in range(0,42):
		switch = random.randint(0,41)
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

def add_join_to_board(game):
	space1 = BoardSpace.get(-6,-1,game)
	space2 = BoardSpace.get(0,-5,game)
	space3 = BoardSpace.get(6,5,game)
	Meeple.add_meeple(game, game.joining, space1)
	Meeple.add_meeple(game, game.joining, space2)
	Meeple.add_meeple(game, game.joining, space3)
	space4 = BoardSpace.get(-6,-5,game)
	space5 = BoardSpace.get(6,1,game)
	space6 = BoardSpace.get(0,5,game)
	Meeple.add_meeple(game, game.hosting, space4)
	Meeple.add_meeple(game, game.hosting, space5)
	Meeple.add_meeple(game, game.hosting, space6)

def initial_deal(game):
	deck = game.deck.order_by(Card.position)
	for x in range(0,6):
		if x % 2 == 0:
			deck[x].player = game.hosting
		else:
			deck[x].player = game.joining

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
	player = Player.query.filter_by(username=request.authorization.username).first()
	result = player_schema.dump(player)
	return jsonify(result.data)

@app.route("/player/", methods=['POST'])
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
	games = Game.query.with_entities(Game.id, Game.status).\
		filter(Game.status != 'In Progress').all()
	stuff = games_schema.dump(games)
	return jsonify({"games":stuff.data})

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
	result = game_schema.dump(data)
	return jsonify({'result':result.data})

@app.route("/game/<int:game_id>", methods=['GET'])
@requires_auth
def get_game(game_id):
	'''
	Get information on game
	'''
	game = Game.query.filter_by(id=game_id).first()
	result = game_schema.dump(game)
	return jsonify(result.data)

@app.route("/game/<int:game_id>", methods=['POST'])
@requires_auth
def join_game(game_id):
	'''
	Join the game_id
	'''
	game = Game.query.filter_by(id=game_id).first()
	if not game:
		return "Game does not exist"

	if game.joining:
		return "Already Full"
	player = Player.query.filter_by(username=request.authorization.username).first()
	if game.hosting  == player:
		return "Cannot Join your own game"
	game.joining = player
	game.status = "In Progress"
	game.turn = game.hosting
	add_join_to_board(game)
	initial_deal(game)
	db.session.commit()
	return 'Join %d' % game_id

@app.route("/game/<int:game_id>/hand", methods=["GET"])
@requires_auth
@requires_game_auth
def get_hand(game_id):
	player = Player.query.filter_by(username=request.authorization.username).first()
	hand = Card.query.filter_by(game_id=game_id).filter_by(player=player).all()
	result = cards_schema.dump(hand)
	return jsonify({'hand':result.data})

@app.route("/game/<int:game_id>/meeples", methods=["GET"])
@requires_auth
@requires_game_auth
def get_meeples(game_id):
	player = Player.query.filter_by(username=request.authorization.username).first()
	meeples = Meeple.query.filter_by(game_id=game_id).filter_by(player=player).all()
	result = meeples_schema.dump(meeples)
	return jsonify({'meeples':result.data})

@app.route("/game/<int:game_id>/draw", methods=['GET'])
@requires_auth
@requires_turn_auth
def draw_card(game_id):
	card = Card.query.filter_by(game_id=game_id).filter_by(player_id=None).\
		filter_by(board_space_id=None).filter_by(finished = False).\
		order_by(Card.position).first()
	player = Player.query.filter_by(username=request.authorization.username).first()
	card.player = player
	end_turn(game_id)
	db.session.commit()
	result = card_schema.dump(card)
	return jsonify(result.data)

@app.route("/game/<int:game_id>/move/<int:meeple_id>", methods=['POST'])
@requires_auth
@requires_turn_auth 
@meeple_check
def move_meeple(game_id, meeple_id):
	json = request.get_json()
	data, errors = boardspace_schema.load(json)
	board_space = BoardSpace.query.filter_by(game_id=game_id).filter_by(x_loc=data.x_loc).\
		filter_by(y_loc=data.y_loc).first()
	meeple = Meeple.query.filter_by(game_id=game_id).filter_by(id=meeple_id).first()
	
	#Check to make sure space exists
	if not board_space:
		return jsonify({'error':'This is not a space.'})
	
	#Check that movement is allowed
	x_move = meeple.board_space.x_loc - board_space.x_loc
	y_move = meeple.board_space.y_loc - board_space.y_loc
	if (abs(x_move) > 1 or abs(y_move) > 1 or abs(x_move - y_move) > 1):
		return jsonify({'error':'This is an illegal move.'})

	#Check that space is empty
	if board_space.meeple or board_space.card:
		return jsonify({'error':'This space is already occupied son.'})
	
	#Place meeple at new space
	board_space.meeple = meeple

	#Change to other players turn
	end_turn(game_id)

	db.session.commit()
	result = meeple_schema.dump(meeple)
	return jsonify(result.data)

@app.route("/game/<int:game_id>/hand/<int:card_id>", methods=['POST'])
@requires_auth
@requires_turn_auth 
@card_check
def play_card(game_id, card_id):
	json = request.get_json()
	data, errors = boardspace_schema.load(json)
	board_space = BoardSpace.query.filter_by(game_id=game_id).filter_by(x_loc=data.x_loc).\
		filter_by(y_loc=data.y_loc).first()
	player = Player.query.filter_by(username=request.authorization.username).first()
	meeples = Meeple.query.filter_by(game_id=game_id).filter_by(player=player).all()
	card = Card.query.filter_by(game_id=game_id).filter_by(id=card_id).first()

	if not board_space:
		return jsonify({'error':'This is not a space.'})

	#Check that movement is allowed
	illegal = True
	for meeple in meeples:
		#Check that movement is allowed
		x_move = meeple.board_space.x_loc - board_space.x_loc
		y_move = meeple.board_space.y_loc - board_space.y_loc
		if (abs(x_move) > 1 or abs(y_move) > 1 or abs(x_move - y_move) > 1):
			pass
		else:
			illegal = False
	
	if illegal:
		return jsonify({'error':'This is an illegal move.'})

	if board_space.meeple or board_space.card:
		return jsonify({'error':'This space is already occupied son.'})

	card.player = None
	card.board_space = board_space
	end_turn(game_id)
	db.session.commit()
	result = card_schema.dump(card)
	return jsonify(result.data)

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