from ..core import Service
from ..models import Player
from ..schema import PlayerSchema

class PlayerService(Service):
	__model__ = Player
	__schema__ = PlayerSchema()