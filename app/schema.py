from marshmallow import Schema, fields, post_load
from .models import Game, Card, BoardSpace, Player, Meeple

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
		data['status'] = 'starting'
		return Game(**data)

	def game_info(self, data):
		result = self.dump(data)
		try:
			del result.data['deck']
		except:
			for x in result.data:
				del x['deck']
		return result

class BoardSpaceSchema(Schema):
	x_loc = fields.Int()
	y_loc = fields.Int()
	card = fields.Nested('CardSchema', many=False)
	meeple = fields.Nested('MeepleSchema', many=False, exclude=('board_space',))

	@post_load
	def make_boardspace(self, data):
		return BoardSpace(**data)

class CardSchema(Schema):
	value = fields.Str()

	@post_load
	def make_card(self, data):
		return Card(**data)

class MeepleSchema(Schema):
	id = fields.Int()
	player = fields.Nested(PlayerSchema, only=["id", "username"])
	board_space = fields.Nested(BoardSpaceSchema, only=["x_loc", "y_loc"])