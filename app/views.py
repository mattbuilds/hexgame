from . import app
from flask import jsonify, request

@app.route("/", methods=['GET', 'POST'])
def hello():
	post = request.get_json(force=True)
	print post['id']
	return jsonify(post)

@app.route("/game", methods=['GET'])
def get_games():
	'''
	Returns a list of all games
	'''
	return "Hello"

@app.route("/game", methods=['POST'])
def create_game():
	'''
	Create a new game
	'''
	return "Sup"

@app.route("/game/<int:game_id>", methods=['GET'])
def get_game(game_id):
	'''
	Get information on game
	'''
	return 'Get %d' % game_id

@app.route("/game/<int:game_id>", methods=['POST'])
def join_game(game_id):
	'''
	Join the game_id
	'''
	return 'Join %d' % game_id

@app.route("/game/<int:game_id>/deal", methods=['GET'])
def deal_hand(game_id):
	return 'Get %d' % game_id

@app.route("/game/<int:game_id>/draw", methods=['POST'])
def draw_card(game_id):
	return 'Post %d' % game_id

@app.route("/game/<int:game_id>/move/<int:meeple_id>", methods=['POST'])
def move_meeple(game_id, meeple_id):
	return 'Post %d %d' % (game_id, meeple_id)

@app.route("/game/<int:game_id>/play/<int:meeple_id>", methods=['POST'])
def play_card(game_id, meeple_id):
	return 'Post %d %d' % (game_id, meeple_id)

@app.route("/game/<int:game_id>/submit", methods=['POST'])
def move_meeple(game_id, meeple_id):
	return 'Post %d' % game_id