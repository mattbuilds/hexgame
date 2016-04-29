import random
from . import app, db
from flask import Response, jsonify, request
from .models import Game, Card, BoardSpace, Player, Meeple
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
				if ((x==0 and y==0) or (x==1 and y==1)):
					Meeple.add_meeple(game, game.hosting, space)

def add_join_to_board(game):
	space1 = BoardSpace.get(2,2,game)
	space2 = BoardSpace.get(2,3,game)
	Meeple.add_meeple(game, game.joining, space1)
	Meeple.add_meeple(game, game.joining, space2)


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

@app.route("/test", methods=['GET'])
def test():
	return "Test"

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
	games = Game.query.with_entities(Game.id, Game.status).all()
	result = games_schema.dump(games)
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
					  filter_by(board_space_id=None).order_by(Card.position).first()
	player = Player.query.filter_by(username=request.authorization.username).first()
	card.player = player
	Game.change(game_id)
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
	if (abs(meeple.board_space.x_loc - board_space.x_loc) > 1 or 
		abs(meeple.board_space.y_loc - board_space.y_loc) > 1):
		return jsonify({'error':'This is an illegal move.'})

	#Check that space is empty
	if board_space.meeple or board_space.card:
		return jsonify({'error':'This space is already occupied son.'})
	
	#Place meeple at new space
	board_space.meeple = meeple

	db.session.commit()
	result = meeple_schema.dump(meeple)
	return jsonify(result.data)

@app.route("/game/<int:game_id>/play/<int:meeple_id>/<int:card_id>", methods=['POST'])
@requires_auth
@requires_turn_auth 
@meeple_check
@card_check
def play_card(game_id, meeple_id, card_id):
	json = request.get_json()
	data, errors = boardspace_schema.load(json)
	board_space = BoardSpace.query.filter_by(game_id=game_id).filter_by(x_loc=data.x_loc).\
								   filter_by(y_loc=data.y_loc).first()
	meeple = Meeple.query.filter_by(game_id=game_id).filter_by(id=meeple_id).first()
	card = Card.query.filter_by(game_id=game_id).filter_by(id=card_id).first()

	if not board_space:
		return jsonify({'error':'This is not a space.'})

	#Check that movement is allowed
	if (abs(meeple.board_space.x_loc - board_space.x_loc) > 1 or 
		abs(meeple.board_space.y_loc - board_space.y_loc) > 1):
		return jsonify({'error':'This is an illegal move.'})

	if board_space.meeple or board_space.card:
		return jsonify({'error':'This space is already occupied son.'})

	card.player = None
	board_space.card = card
	db.session.commit()
	result = card_schema.dump(card)
	return jsonify(result.data)