from ..core import Service, ResponseError
from ..models import BoardSpace
from ..schema import BoardSpaceSchema

class BoardSpaceService(Service):
	__model__ = BoardSpace
	__schema__ = BoardSpaceSchema()

	def move_meeple(self, request, game_id, meeple):
		board_space = self.__get_first(request, game_id)
		if self.__check_legal(board_space, meeple):
			board_space.meeple = meeple
			response = self.__schema__.dump(board_space)
			return response.data
		else:
			raise ResponseError('This is an illegal move.')

	def play_card(self, request, game_id, meeples, card):
		board_space = self.__get_first(request, game_id)
		for meeple in meeples:
			if self.__check_legal(board_space, meeple):
				card.player=None
				board_space.card = card
				response = self.__schema__.dump(board_space)
				return response.data
		raise ResponseError('This is an illegal move.')

	def __get_first(self, request, id):
		data = self.parse_request(request)
		result = self.get(game_id=id, x_loc=data.x_loc, y_loc=data.y_loc)
		if not result:
			raise ResponseError('This is not a space.')
		if result.meeple or result.card:
			raise ResponseError('This space is already occupied.') 
		return result

	def __check_legal(self, board_space, meeple):
		x_move = meeple.board_space.x_loc - board_space.x_loc
		y_move = meeple.board_space.y_loc - board_space.y_loc
		if (abs(x_move) > 1 or abs(y_move) > 1 or abs(x_move - y_move) > 1):
			return False
		else:
			return True