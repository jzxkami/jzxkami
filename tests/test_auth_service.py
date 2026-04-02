from pathlib import Path

from app.services.auth_service import AuthService


def test_register_login_getuser_logout(tmp_path: Path):
    db_path = tmp_path / "auth_test.db"
    service = AuthService(db_path=db_path, token_ttl_hours=1)

    user = service.register_user("tester_01", "pass1234")
    assert user.user_id > 0
    assert user.username == "tester_01"

    session = service.login("tester_01", "pass1234")
    assert session.access_token

    current = service.get_user_by_token(session.access_token)
    assert current is not None
    assert current.username == "tester_01"

    service.logout(session.access_token)
    assert service.get_user_by_token(session.access_token) is None


def test_register_duplicate_username(tmp_path: Path):
    db_path = tmp_path / "auth_test_dup.db"
    service = AuthService(db_path=db_path, token_ttl_hours=1)

    service.register_user("dup_user", "pass1234")

    try:
        service.register_user("dup_user", "pass1234")
        raised = False
    except ValueError:
        raised = True

    assert raised is True


def test_login_wrong_password(tmp_path: Path):
    db_path = tmp_path / "auth_test_wrong.db"
    service = AuthService(db_path=db_path, token_ttl_hours=1)

    service.register_user("normal_user", "pass1234")

    try:
        service.login("normal_user", "wrongpass")
        raised = False
    except ValueError:
        raised = True

    assert raised is True
