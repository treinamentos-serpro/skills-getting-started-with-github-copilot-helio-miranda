from fastapi.testclient import TestClient

from src.app import activities, app

client = TestClient(app)


def _cleanup_signup(activity_name: str, email: str) -> None:
    if email in activities.get(activity_name, {}).get("participants", []):
        client.delete(f"/activities/{activity_name}/signup?email={email}")


def test_get_activities_returns_activity_data():
    response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert "participants" in payload["Chess Club"]
    assert isinstance(payload["Chess Club"]["participants"], list)


def test_signup_success_registers_student():
    activity_name = "Soccer Club"
    email = "new.student@example.com"
    _cleanup_signup(activity_name, email)

    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    assert email in client.get("/activities").json()[activity_name]["participants"]

    _cleanup_signup(activity_name, email)


def test_signup_duplicate_student_fails():
    activity_name = "Chess Club"
    email = "duplicate.student@example.com"
    _cleanup_signup(activity_name, email)

    first_response = client.post(f"/activities/{activity_name}/signup?email={email}")
    second_response = client.post(f"/activities/{activity_name}/signup?email={email}")

    assert first_response.status_code == 200
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Student already signed up for this activity"

    _cleanup_signup(activity_name, email)


def test_signup_activity_not_found_fails():
    response = client.post("/activities/Unknown Activity/signup?email=student@example.com")

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_when_activity_is_full_fails():
    activity_name = "Soccer Club"
    original_participants = activities[activity_name]["participants"][:]

    try:
        activities[activity_name]["participants"] = [
            f"full.{index}@example.com" for index in range(activities[activity_name]["max_participants"])
        ]

        response = client.post(f"/activities/{activity_name}/signup?email=student@example.com")

        assert response.status_code == 400
        assert response.json()["detail"] == "Activity is full"
    finally:
        activities[activity_name]["participants"] = original_participants


def test_cancel_signup_removes_participant():
    activity_name = "Chess Club"
    email = "student.test@example.com"
    _cleanup_signup(activity_name, email)

    post_response = client.post(f"/activities/{activity_name}/signup?email={email}")
    cancel_response = client.delete(f"/activities/{activity_name}/signup?email={email}")

    assert post_response.status_code == 200
    assert cancel_response.status_code == 200
    assert cancel_response.json()["message"] == f"Canceled signup for {email} in {activity_name}"
    assert email not in client.get("/activities").json()[activity_name]["participants"]


def test_cancel_signup_for_unregistered_student_fails():
    activity_name = "Chess Club"
    email = "missing.student@example.com"

    response = client.delete(f"/activities/{activity_name}/signup?email={email}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found in this activity"
