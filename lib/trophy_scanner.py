"""Functionality for parsing IZGC thread for new trophies"""

import json
import re

from lib.thread_reader import Thread
from lib.firebase_handler import FirebaseHandler
from lib.helpers import datetime_formatted_est

fb_handler = FirebaseHandler()


def update_trophy_dict(existing_trophies, new_trophies):
    for game, game_trophies in new_trophies.items():
        if game not in existing_trophies:
            existing_trophies[game] = game_trophies
        else:
            existing_trophies[game].update(game_trophies)


class TrophyReporter:
    def __init__(self, imp_trophies):
        self.trophy_log_file = "trophy_timestamps.json"
        self.imp_trophies = imp_trophies
        self.trophy_log = self.read_trophy_log_file()

    def read_trophy_log_file(self):
        try:
            with open(self.trophy_log_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def write_trophy_log_to_file(self):
        with open(self.trophy_log_file, "w", encoding="utf-8") as file:
            json.dump(self.trophy_log, file, indent=2)

    def report_new_trophies(self):
        if not self.imp_trophies:
            print("No new trophies found.")
            return

        print("\n******** NEW TROPHIES ********")
        for imp, trophies in self.imp_trophies.items():
            fb_handler.write_trophies_to_db(imp, trophies)
            # ugly gross way to remove db references, for now
            for game, game_trophies in trophies.items():
                for _game_trophy, data in game_trophies.items():
                    del data["reference"]
                    # convert timestamp into friendly string
                    data["timestamp"] = datetime_formatted_est(
                        data["timestamp"])

            if imp not in self.trophy_log:
                new_member_string = " (New Club member!)"
                self.trophy_log[imp] = trophies
            else:
                new_member_string = ""
                update_trophy_dict(self.trophy_log[imp], trophies)

            print(f"{imp}{new_member_string}:")
            for game, trophy in trophies.items():
                for name, post in trophy.items():
                    print(f"  [{game}] {name} -- posted {post['timestamp']}")
                    print(f"  {post['link']}\n")

            self.write_trophy_log_to_file()


class IZGCThread(Thread):
    """Thread with additional functionality for trophy scanning"""
    def __init__(self, *, dispatcher, year_override=None):
        self.dispatcher = dispatcher
        if year_override:
            fb_handler.year = year_override
        super().__init__(
            dispatcher=dispatcher,
            thread_id=dispatcher.config["DEFAULT"]["izgc_thread_id"]
        )

    def trophy_scan(self):
        post_list = self.new_posts()
        imp_trophies = {}

        for post in post_list:
            post.remove_quotes()
            post_trophies = self.get_post_trophies(post)
            if post_trophies:
                if post.username not in imp_trophies:
                    imp_trophies[post.username] = post_trophies
                else:
                    update_trophy_dict(
                        imp_trophies[post.username], post_trophies)

        return imp_trophies

    def get_post_trophies(self, post):
        earned_trophies = {}
        images = post.image_urls()
        for image in images:
            for trophy_path, trophy_data in \
                    fb_handler.eligible_trophies.items():
                if re.search(trophy_path, image):
                    # only record trophies in valid time windows
                    if not self.valid_post_timestamp(
                            trophy_data, post.timestamp):
                        continue

                    new_trophy = {trophy_data["game"]: {
                        trophy_data["name"]: {
                            "timestamp": post.timestamp,
                            "link": post.link,
                            "reference": trophy_data["reference"]
                        }}}

                    update_trophy_dict(earned_trophies, new_trophy)

        return earned_trophies

    @staticmethod
    def valid_post_timestamp(trophy_data, post_timestamp):
        if (
                trophy_data['start_time'] <
                post_timestamp <
                trophy_data['end_time']
        ):
            return True

        for window in fb_handler.all_trophies_event_windows:
            if window['start_time'] < post_timestamp < window['end_time']:
                return True

        return False
