import pytest
import tempfile
import app as flaskr

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