from app.card import CardService
from app.player  import PlayerService
from app.boardspace import BoardSpaceService
from app.meeple import MeepleService
from app.models import Game, Card, BoardSpace, Meeple
from .. import db
from ..core import ResponseError

_card = CardService()
_player = PlayerService()
_boardspace = BoardSpaceService()
_meeple = MeepleService()

class Turn():
	def test_turn(self):
		return "Hello"

	def draw_card(self, request, game_id):
		card = _card.draw(
			game_id,
			_player.get(username=request.authorization.username))
		self.__check_move(game_id)
		db.session.commit()
		return card

	def move_meeple(self, request, game_id, meeple_id):
		try:
			player = _player.get(username=request.authorization.username)
			board_space = _boardspace.move_meeple(
				request, 
				game_id,
				_meeple.get(game_id=game_id, id=meeple_id))
			if board_space.end_space_id:
				game = Game.query.filter_by(id=game_id).first()
				game.status = 'Done'
				game.winner = player
				db.session.commit()
				return 'Done'
			self.__check_move(game_id)
			db.session.commit()
			return board_space
		except ResponseError as e:
			return e.error

	def play_card(self, request, game_id, card_id):
		try:
			player = _player.get(username=request.authorization.username)
			result = _boardspace.play_card(
				request,
				game_id,
				_meeple.all(game_id=game_id, player=player),
				_card.get(game_id=game_id, id=card_id))
			self.__check_move(game_id)
			db.session.commit()
			return result
		except ResponseError as e:
			return e.error

	def __get_movement(self, value):
		switcher = {
			'U': (0,1),
			'UR': (1,1),
			'DR': (1,0),
			'D':(0,-1),
			'DL':(-1,-1),
			'UL':(-1,0)
		}
		return switcher.get(value, "nothing")

	def __get_opposite_direction(self, value):
		switcher = {
			'U' : 'D',
			'UR': 'DL',
			'DR': 'UL',
			'D':'U',
			'DL':'UR',
			'UL':'DR'
		}
		return switcher.get(value, "nothing")

	def __check_move(self, game_id):
		game = Game.query.filter_by(id=game_id).first()
		if game.move_count > 0:
			self.__end_turn(game_id)
			game.move_count = 0
		else:
			game.move_count += 1

	def __end_turn(self, game_id):
		"""Function that is called at the end of every turn

		The purpose of this function is to handle pieces moving after a completed turn
		The piece will be moves, rotated, and scored
		(Right now is very long, should probably be broken down)
		"""
		# Makes sure change are in the databse
		# TODO: consider persist object through instead of flushing to db
		db.session.flush()

		#Get all cards that have potential to move
		cards = Card.query.filter_by(game_id=game_id).\
				filter_by(value="P").\
				filter(Card.board_space_id != None).\
				all()
		#Move all the cards
		for card in cards:
			x_y = self.__get_movement(card.direction)
			new_space = BoardSpace.query.filter_by(game_id=game_id).\
				filter_by(x_loc = card.board_space.x_loc + x_y[0]).\
				filter_by(y_loc = card.board_space.y_loc + x_y[1]).\
				first()

			#if no space, flip in opposite direction
			if not new_space:
				card.direction = self.__get_opposite_direction(card.direction)
			else:
				previous_space = card.board_space
				card.board_space = new_space

				#if current space, rotate
				current_space = Card.query.filter_by(game_id=game_id).\
					filter_by(board_space=new_space).filter(Card.value != "P").\
					filter(Card.id != card.id).first()
				if current_space:
					card.direction = current_space.value
					current_space.board_space = None
					current_space.finished = True

				#Grab any meeples at current space, if they exist add points to score, then remove
				meeple = Meeple.query.filter_by(game_id=game_id).\
					filter_by(board_space=new_space).first()
				
				if meeple:
					meeple.board_space = None
					meeple.finished = True
					card.board_space = None
					card.finished = True

			#flush so duplicate distruction of meeple does not happen
			db.session.flush()

		#End Turn 
		Game.change(game_id)
