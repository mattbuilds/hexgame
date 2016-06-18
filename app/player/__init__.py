from ..core import Service
from ..models import Player
from ..schema import PlayerSchema, GeneratePlayerSchema
import random
import string

class PlayerService(Service):
	__model__ = Player
	__schema__ = PlayerSchema()
	__generate_schema__ = GeneratePlayerSchema()

	def generate(self):
		username = self.__random_string(10)
		password = self.__random_string(10)
		player = self.__model__(
			username = username,
			password = password)
		self.create(player)
		result = self.__generate_schema__.dump(player)
		return result.data

	def __random_string(self, length):
		s = string.lowercase + string.digits + string.uppercase
		return ''.join(random.choice(s) for i in range(length))