"""Utilities for managing configuration and logging in to forums"""

import configparser
import os

import requests


class InvalidConfigError(Exception):
    pass


class Dispatcher:
    # May need to eventually refactor this into separate request handler and
    # config handler classes.
    SA_URL = "https://forums.somethingawful.com/"
    CONFIG_FILE = "config.ini"

    def __init__(self):
        self.session = requests.Session()
        self.config = configparser.ConfigParser(interpolation=None)
        if not os.path.isfile(self.CONFIG_FILE):
            raise InvalidConfigError(f"{self.CONFIG_FILE} is missing!")
        self.config.read(self.CONFIG_FILE)
        self.logged_in = False
        self.default_thread = self.config["DEFAULT"]["izgc_thread_id"]

    def check_sa_creds(self):
        if "username" not in self.config["DEFAULT"] \
                or "password" not in self.config["DEFAULT"] \
                or self.config["DEFAULT"]["username"] == "" \
                or self.config["DEFAULT"]["password"] == "":
            raise InvalidConfigError(
                f"username and password not present in {self.CONFIG_FILE}.")

    def login(self, required=True):
        if self.logged_in:
            return

        try:
            self.check_sa_creds()
        except InvalidConfigError:
            if required:
                raise

            print(
                "Warning! Cannot proceed with login, continuing as " +
                "anonymous user."
            )
            return

        info = {"username": self.config["DEFAULT"]["username"],
                "password": self.config["DEFAULT"]["password"],
                "action": "login"
                }
        self.session.post(
            f"{self.SA_URL}account.php", data=info)
        self.logged_in = True

    def get_thread(self, **kwargs):
        return self.session.get(f"{self.SA_URL}showthread.php", **kwargs)

    def save_config(self):
        with open(self.CONFIG_FILE, "w", encoding="utf-8") as file:
            self.config.write(file)
