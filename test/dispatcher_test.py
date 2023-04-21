import pytest

import dispatcher


@pytest.fixture(name="dis")
def fixture_dis():
    return dispatcher.Dispatcher()


class TestInit:
    def test_missing_config_file_errors(self, mocker):
        mocker.patch("dispatcher.os.path.isfile", return_value=False)
        with pytest.raises(dispatcher.InvalidConfigError):
            dispatcher.Dispatcher()

    def test_init_reads_config(self, mocker):
        read = mocker.patch("dispatcher.configparser.ConfigParser.read")
        dispatch = dispatcher.Dispatcher()
        read.assert_called_once_with(dispatch.CONFIG_FILE)


class TestCheckSACreds:
    def test_missing_username_errors(self, dis):
        dis.config["DEFAULT"] = {"password": "MakesYouStupid"}
        with pytest.raises(dispatcher.InvalidConfigError):
            dis.check_sa_creds()

    def test_missing_password_errors(self, dis):
        dis.config["DEFAULT"] = {"username": "Jeffery"}
        with pytest.raises(dispatcher.InvalidConfigError):
            dis.check_sa_creds()

    def test_blank_username_errors(self, dis):
        dis.config["DEFAULT"] = {"username": "", "password": "MakesYouStupid"}
        with pytest.raises(dispatcher.InvalidConfigError):
            dis.check_sa_creds()

    def test_blank_password_errors(self, dis):
        dis.config["DEFAULT"] = {"username": "Jeffery", "password": ""}
        with pytest.raises(dispatcher.InvalidConfigError):
            dis.check_sa_creds()

    def test_valid_sa_creds(self, dis):
        dis.config["DEFAULT"] = {
            "username": "Jeffery", "password": "MakesYouStupid"}
        dis.check_sa_creds()


class TestLogin:
    def test_non_required_invalid_creds(self, dis, mocker, capsys):
        mocker.patch("dispatcher.Dispatcher.check_sa_creds")
        dispatcher.Dispatcher.check_sa_creds.side_effect = \
            dispatcher.InvalidConfigError()
        dis.login(required=False)
        assert capsys.readouterr().out != ""

    def test_required_invalid_creds(self, dis, mocker):
        mocker.patch("dispatcher.Dispatcher.check_sa_creds")
        dispatcher.Dispatcher.check_sa_creds.side_effect = \
            dispatcher.InvalidConfigError()
        with pytest.raises(dispatcher.InvalidConfigError):
            dis.login()

    def test_login_posts(self, dis, mocker):
        post = mocker.patch("dispatcher.requests.Session.post")
        dis.config["DEFAULT"] = {
            "username": "Jeffery", "password": "MakesYouStupid"}
        dis.login()
        post.assert_called_once()


# These last two functions are very simple, so just assert that they do
# an expected action for now
def test_get_thread_gets(dis, mocker):
    get = mocker.patch("dispatcher.requests.Session.get")
    dis.get_thread()
    get.assert_called_once()


def test_save_config_writes(dis, mocker):
    write = mocker.patch("dispatcher.configparser.ConfigParser.write")
    mocker.patch("builtins.open", mocker.mock_open(read_data=""))
    dis.save_config()
    write.assert_called_once()
