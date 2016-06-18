from ..core import Service, ResponseError
from ..models import Card
from ..schema import CardSchema

class CardService(Service):
	__model__ = Card
	__schema__ = CardSchema()
	__schema_many__ = CardSchema(many=True)

	def draw(self, game_id, player):
		card = self.__model__.query.filter_by(game_id=game_id).filter_by(player_id=None).\
			filter_by(board_space_id=None).filter_by(finished = False).\
			order_by(Card.position).first()
		card.player = player
		result = self.__schema__.dump(card)
		return result.data
