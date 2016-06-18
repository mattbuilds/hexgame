from . import db
from sqlalchemy.exc import IntegrityError
from flask import Response, jsonify, request

class ParseException(Exception):
	"""Exception on parse errors"""
	def __init__(self, error, code):
		self.error = error
		self.code = code

class ResponseError(Exception):
	def __init__(self, error):
		self.error = {'error':error}

class Service(object):
	__model__ = None
	__schema__ = None
	__schema_many__ = None

	def parse_request(self, request):
		json = request.get_json()
		data,errors = self.__schema__.load(json)
		if errors:
			raise ParseException(errors,422)
		return data

	def all(self, **kwargs):
		return self.__model__.query.filter_by(**kwargs).all()

	def all_response(self, **kwargs):
		result = self.all(**kwargs)
		response = self.__schema_many__.dump(result)
		return jsonify(response.data)

	def get(self,**kwargs):
		return self.__model__.query.filter_by(**kwargs).first()

	def get_response(self, **kwargs):
		result = self.get(**kwargs)
		response = self.__schema__.dump(result)
		return jsonify(response.data)

	def create_request(self, request):
		data = self.parse_request(request)
		created = self.create(data)
		result = self.__schema__.dump(created)
		return jsonify(result.data)

	def create(self, data):
		try:
			db.session.add(data)
			db.session.commit()
		except IntegrityError:
			return dict(error = "This resource already exists")
		return data