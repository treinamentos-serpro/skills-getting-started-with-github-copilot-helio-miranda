from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)


def test_cancel_signup_removes_participant():
    activity_name = "Chess Club"
    email = "student.test@example.com"

    # ensure clean state
    activity = client.get("/activities").json()[activity_name]
    if email in activity["participants"]:
        client.delete(f"/activities/{activity_name}/signup?email={email}")

    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 200

    cancel_response = client.delete(f"/activities/{activity_name}/signup?email={email}")
    assert cancel_response.status_code == 200
    assert email not in client.get("/activities").json()[activity_name]["participants"]


def test_cancel_signup_for_unregistered_student_fails():
    activity_name = "Chess Club"
    email = "missing.student@example.com"

    response = client.delete(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found in this activity"
