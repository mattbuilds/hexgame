import os
import pytest
import tempfile
import app as flaskr
import json
from mock import Mock
from app import views, auth, services
from flask import request
from base64 import b64encode

@pytest.fixture(scope="session")
def original(request):
	db_fd, flaskr.app.config['DATABASE'] = tempfile.mkstemp()
	flaskr.app.config['TESTING'] = True
	client = flaskr.app.test_client()
	with flaskr.app.app_context():
		flaskr.init_db()

	def teardown():
		os.close(db_fd)
		os.unlink(flaskr.app.config['DATABASE'])
	request.addfinalizer(teardown)
	return client

@pytest.fixture(scope="function")
def client(original, request):
	client = original
	check_auth = auth.check_auth
	get_response = services.player.get_response

	def teardown():
		auth.check_auth = check_auth
		services.player.get_response =  get_response
	request.addfinalizer(teardown)
	return client

def test_get_games(client):
	auth.check_auth = Mock(return_value=True)
	services.game.get_open_games = Mock(return_value={'games':[]})
	response = client.get('/game')
	assert response.status_code == 200
	assert json.loads(response.data) == {'games':[]}

def test_get_player_no_auth(client):
	username = 'matt'
	password = 'test'
	headers = {
		'Authorization': 'Basic ' + b64encode("{0}:{1}".format(username, password))
	}
	auth.check_auth = Mock(return_value=False)
	response = client.get('/player/', headers=headers)
	assert response.status_code == 401
	assert json.loads(response.data) == {'message': "Authentication Required"}

def test_get_player_auth(client):
	username = 'matt'
	password = 'test'
	headers = {
		'Authorization': 'Basic ' + b64encode("{0}:{1}".format(username, password))
	}
	auth.check_auth = Mock(return_value=True)
	services.player.get_response = Mock(return_value=json.dumps({'id':1,'username':'matt'}))
	response = client.get('/player/', headers=headers)
	assert response.status_code == 200
	assert json.loads(response.data) == {'id':1,'username':'matt'}

def test_get_game_no_username(client):
	username = 'mattsss'
	password = 'test'
	headers = {
		'Authorization': 'Basic ' + b64encode("{0}:{1}".format(username, password))
	}
	response = client.get('/player/', headers=headers)
	assert response.status_code == 401
	assert json.loads(response.data) == {'message': "Authentication Required"}

def test_get_game_no_auth(client):
	auth.check_auth = Mock(return_value=False)
	response = client.get('/game/1')
	assert response.status_code == 401
	assert json.loads(response.data) == {'message': "Authentication Required"}

def test_get_movement_u(client):
	movement = views.get_movement('U')
	assert movement == (0,1)

def test_get_movement_ur(client):
	movement = views.get_movement('UR')
	assert movement == (1,1)

def test_get_movement_ul(client):
	movement = views.get_movement('UL')
	assert movement == (-1,0)

def test_get_movement_d(client):
	movement = views.get_movement('D')
	assert movement == (0,-1)

def test_get_movement_dr(client):
	movement = views.get_movement('DR')
	assert movement == (1,0)

def test_get_movement_dl(client):
	movement = views.get_movement('DL')
	assert movement == (-1,-1)

def test_get_movement_nothing(client):
	movement = views.get_movement('F')
	assert movement == 'nothing'