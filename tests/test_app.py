from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client():
	with TestClient(app_module.app) as test_client:
		yield test_client


@pytest.fixture(autouse=True)
def restore_activities():
	original_activities = deepcopy(app_module.activities)
	yield
	app_module.activities.clear()
	app_module.activities.update(original_activities)


def activity_endpoint(activity_name, endpoint):
	return f"/activities/{quote(activity_name, safe='')}/{endpoint}"


def test_root_redirects_to_activity_page(client):
	# Arrange

	# Act
	response = client.get("/", follow_redirects=False)

	# Assert
	assert response.status_code == 307
	assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client):
	# Arrange
	expected_activities = deepcopy(app_module.activities)

	# Act
	response = client.get("/activities")

	# Assert
	assert response.status_code == 200
	assert response.json() == expected_activities


def test_signup_adds_participant(client):
	# Arrange
	activity_name = "Basketball Club"
	email = "new.student@mergington.edu"

	# Act
	response = client.post(
		activity_endpoint(activity_name, "signup"),
		params={"email": email},
	)

	# Assert
	assert response.status_code == 200
	assert response.json() == {
		"message": f"Signed up {email} for {activity_name}"
	}
	assert email in app_module.activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client):
	# Arrange
	activity_name = "Chess Club"
	email = app_module.activities[activity_name]["participants"][0]
	original_participants = app_module.activities[activity_name]["participants"].copy()

	# Act
	response = client.post(
		activity_endpoint(activity_name, "signup"),
		params={"email": email},
	)

	# Assert
	assert response.status_code == 400
	assert response.json()["detail"] == "Student already signed up for this activity"
	assert app_module.activities[activity_name]["participants"] == original_participants


def test_signup_rejects_unknown_activity(client):
	# Arrange
	activity_name = "Unknown Club"

	# Act
	response = client.post(
		activity_endpoint(activity_name, "signup"),
		params={"email": "new.student@mergington.edu"},
	)

	# Assert
	assert response.status_code == 404
	assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
	# Arrange
	activity_name = "Chess Club"
	email = app_module.activities[activity_name]["participants"][0]

	# Act
	response = client.delete(
		activity_endpoint(activity_name, "participants"),
		params={"email": email},
	)

	# Assert
	assert response.status_code == 200
	assert response.json() == {
		"message": f"Unregistered {email} from {activity_name}"
	}
	assert email not in app_module.activities[activity_name]["participants"]


def test_unregister_rejects_unknown_activity(client):
	# Arrange
	activity_name = "Unknown Club"

	# Act
	response = client.delete(
		activity_endpoint(activity_name, "participants"),
		params={"email": "new.student@mergington.edu"},
	)

	# Assert
	assert response.status_code == 404
	assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_nonparticipant(client):
	# Arrange
	activity_name = "Basketball Club"
	email = "not.registered@mergington.edu"

	# Act
	response = client.delete(
		activity_endpoint(activity_name, "participants"),
		params={"email": email},
	)

	# Assert
	assert response.status_code == 404
	assert response.json()["detail"] == "Student is not signed up for this activity"
	assert email not in app_module.activities[activity_name]["participants"]
