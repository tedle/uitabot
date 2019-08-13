import uita.database


def test_maintenance(database):
    session = database.add_session("token", 0)
    database.maintenance()
    assert database.get_access_token(session) is None
    # Will fail if this call somehow takes more than 5 seconds
    # But if it does we should re-evaluate what's wrong with this test anyway
    session = database.add_session("token", 5)
    database.maintenance()
    assert database.get_access_token(session) is not None


def test_session(database):
    token = "test_token"
    session = database.add_session(token, 0)
    assert database.get_access_token(session) == token
    database.delete_session(session)
    assert database.get_access_token(session) is None


def test_server_role(database):
    server_id = "12345"
    role_id = "67890"
    assert database.get_server_role(server_id) is None
    database.set_server_role(server_id, role_id)
    assert database.get_server_role(server_id) == role_id
    database.set_server_role(server_id, None)
    assert database.get_server_role(server_id) is None


def test_persistence(tmp_path):
    token = "test_token"
    database_file = tmp_path / "uita.db"
    first_database = uita.database.Database(str(database_file))
    session = first_database.add_session(token, 0)

    second_database = uita.database.Database(str(database_file))
    assert second_database.get_access_token(session) == token
