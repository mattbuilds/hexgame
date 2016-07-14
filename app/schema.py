from marshmallow import Schema, fields, post_load, pre_dump, post_dump
from .models import Game, Card, BoardSpace, Player, Meeple

def remove_cards(data):
	#Removes cards that are in the hand or in the deck
	deck = []
	for card in data.deck:
		if card.finished or card.board_space:
			deck.append(card)

	#Creates a new object for cards and meeples on the board
	data.board_played = {'cards': deck, 'meeples':data.meeple}
	return data

class PlayerSchema(Schema):
	id = fields.Int()
	username = fields.Str(
		required=True,
		error_messages={'required':'username is required'}
	)
	password = fields.Str(
		required=True,
		load_only=True,
		error_messages={'required':'password is required'}
	)
	score = fields.Int(dump_only=True)

	@post_load
	def make_player(self, data):
		return Player(**data)

class GeneratePlayerSchema(PlayerSchema):
	password = fields.Str(
		required=True,
		error_messages={'required':'password is required'}
	)

class GameSchema(Schema):
	id = fields.Int(dump_only=True)
	status = fields.Str()
	hosting = fields.Nested(PlayerSchema, only=["id", "username", "score"])
	joining = fields.Nested(PlayerSchema, only=["id", "username", "score"])
	turn = fields.Nested(PlayerSchema, only=["id", "username"])
	board_played = fields.Nested('BoardPlayed')

	@post_load
	def make_game(self, data):
		data['status'] = 'starting'
		return Game(**data)

	@pre_dump(pass_many=True)
	def combine_board(self, data, many):
		if not many:
			if data.hosting_score:
				data.hosting.score = data.hosting_score
			if data.joining_score:
				data.joining.score = data.joining_score
			data = remove_cards(data)
		return data

	@post_dump(pass_many=True)
	def wrap_many(self, data, many):
		if many:
			return {'games': data}
		else:
			return data

class BoardSpaceSchema(Schema):
	x_loc = fields.Int()
	y_loc = fields.Int()
	card = fields.Nested('GeneralCardSchema', many=True)
	meeple = fields.Nested('MeepleSchema', many=False, exclude=('board_space',))

	@post_load
	def make_boardspace(self, data):
		return BoardSpace(**data)

class GeneralCardSchema(Schema):
	id = fields.Int()
	color = fields.Int()
	value = fields.Str()
	direction = fields.Str()
	finished = fields.Bool()
	board_space = fields.Nested(BoardSpaceSchema, only=["x_loc", "y_loc"])

class CardSchema(GeneralCardSchema):
	@post_load
	def make_card(self, data):
		return Card(**data)

	@post_dump(pass_many=True)
	def wrap_many(self, data, many):
		if many:
			return {'cards':data}
		else:
			return data

class GeneralMeepleSchema(Schema):
	id = fields.Int()
	finished = fields.Bool()
	player = fields.Nested(PlayerSchema, only=["id", "username"])
	board_space = fields.Nested(BoardSpaceSchema, only=["x_loc", "y_loc"])

class MeepleSchema(GeneralMeepleSchema):
	@post_dump(pass_many=True)
	def wrap_many(self, data, many):
		if many:
			return {'meeples':data}
		else:
			return data

class BoardPlayed(Schema):
	meeples = fields.Nested(GeneralMeepleSchema, many=True)
	cards = fields.Nested(GeneralCardSchema, many=True)