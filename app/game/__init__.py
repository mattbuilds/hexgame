import random
from turn import Turn
from .. import db
from ..core import Service
from ..models import Game, Card, BoardSpace, Meeple
from ..schema import GameSchema
from flask import Response, jsonify, request


class GameService(Service):
	__model__ = Game
	__schema__ = GameSchema()
	__schema_many__ = GameSchema(many=True)
	turn = Turn()

	def get_open_games(self):
		result = self.__model__.query.filter(Game.status != 'In Progress').all()
		response = self.__schema_many__.dump(result)
		return response.data

	def create_game(self, request, player):
		data = {'status' : 'starting'}
		game = Game(**data)
		game.hosting = player
		db.session.add(game)
		self.__create_deck(game)
		self.__create_board(game)
		db.session.commit()
		result = self.__schema__.dump(game)
		return jsonify(result.data)

	def join_game(self, game, player):
		if not game:
			return "Game does not exist"
		if game.joining:
			return "Already Full"
		if game.hosting  == player:
			return "Cannot Join your own game"
		game.joining = player
		game.status = "In Progress"
		game.turn = game.hosting
		self.__add_join_to_board(game)
		self.__initial_deal(game)
		self.__add_end_spaces(game)
		db.session.commit()
		return 'Join %d' % game.id

	def __create_deck(self, game):
		card_types = ['UL','U', 'UR', 'DR', 'D', 'DL']
		deck = []
		for x in xrange(0,72):
			value = x % 6
			card = dict(position = x, value=card_types[value], game=game)
			result = Card(**card)
			db.session.add(result)

		color = ['']
		for x in xrange(0,12):
			direction = x % 6
			card = dict(position = 72+ x, value = 'P', direction = card_types[direction],
						game=game, color=x, points=0)
			result = Card(**card)
			db.session.add(result)

		db.session.commit()

		# Kind of hacky, can be made better by calling all the cards in a game at once,
		# update in objects, then commit to the database
		for x in range(0,84):
			switch = random.randint(0,83)
			card1 = Card.query.filter_by(position=x).filter_by(game=game).first()
			card2 = Card.query.filter_by(position=switch).filter_by(game=game).first()
			card1.position = switch
			card2.position = x
			db.session.commit() 

	def __create_board(self, game):
		for x in xrange(-5,6):
			for y in xrange(-4,5):
				if abs(y-x) < 5:
					space = BoardSpace(x_loc = x, y_loc = y, game=game)
					db.session.add(space)

	def __add_join_to_board(self, game):
		space1 = BoardSpace.get(-3,1,game)
		space2 = BoardSpace.get(-4,-2,game)
		space3 = BoardSpace.get(-3,-4,game)
		Meeple.add_meeple(game, game.joining, space1)
		Meeple.add_meeple(game, game.joining, space2)
		Meeple.add_meeple(game, game.joining, space3)
		space4 = BoardSpace.get(3,-1,game)
		space5 = BoardSpace.get(4,2,game)
		space6 = BoardSpace.get(3,4,game)
		Meeple.add_meeple(game, game.hosting, space4)
		Meeple.add_meeple(game, game.hosting, space5)
		Meeple.add_meeple(game, game.hosting, space6)

	def __add_end_spaces(self, game):
		space1 = BoardSpace.get(5,1,game)
		space2 = BoardSpace.get(5,2,game)
		space3 = BoardSpace.get(5,3,game)
		space4 = BoardSpace.get(5,4,game)
		space1.player = game.joining
		space2.player = game.joining
		space3.player = game.joining
		space4.player = game.joining
		space5 = BoardSpace.get(-5,-1,game)
		space6 = BoardSpace.get(-5,-2,game)
		space7 = BoardSpace.get(-5,-3,game)
		space8 = BoardSpace.get(-5,-4,game)
		space5.player = game.hosting
		space6.player = game.hosting
		space7.player = game.hosting
		space8.player = game.hosting

	def __initial_deal(self, game):
		deck = game.deck.order_by(Card.position)
		for x in range(0,14):
			if x % 2 == 0:
				deck[x].player = game.hosting
			else:
				deck[x].player = game.joining