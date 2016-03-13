from functools import wraps
from flask import jsonify, request
from .models import Player

def check_auth(username, password):
    return Player().check_password(username, password)

def authenticate():
    message = {'message': "Authentication Required"}
    resp = jsonify(message)

    resp.status_code = 401
    resp.headers['WWW-Authenticate'] = 'Basic realm="Example"'

    return resp

def requires_auth(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		auth = request.authorization
		if not auth or not check_auth(auth.username, auth.password): 
			return authenticate()
		return f(*args, **kwargs)
	return decorated