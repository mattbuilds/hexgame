from ..core import Service, ResponseError
from ..models import Meeple
from ..schema import MeepleSchema

class MeepleService(Service):
	__model__ = Meeple
	__schema__ = MeepleSchema()
	__schema_many__ = MeepleSchema(many=True)