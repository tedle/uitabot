import pytest

import uita.config
import uita.database
import uita.utils
import uita.types


@pytest.fixture
def config(data_dir):
    return uita.config.load(str(data_dir / "config.test.json"))


@pytest.fixture
def database(config):
    return uita.database.Database(config.bot.database)


@pytest.fixture(autouse=True)
def patch_install_dir(tmp_path, monkeypatch):
    assert uita.utils.install_dir.__annotations__["return"] == str
    monkeypatch.setattr(uita.utils, "install_dir", lambda: str(tmp_path))


@pytest.fixture
def data_dir(request):
    return request.config.rootdir / "test" / "data"


@pytest.fixture
def user():
    return uita.types.DiscordUser("1234567890", "name", "http://example.com/img.png", None)
