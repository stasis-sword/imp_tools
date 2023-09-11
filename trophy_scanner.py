"""Functionality for parsing IZGC thread for new trophies"""

import json
import re

from bs4 import BeautifulSoup

from thread_reader import Thread
from firebase_handler import FirebaseHandler


fb_handler = FirebaseHandler()


# now deprecated, instead reading trophy data from firebase db
def get_izgc_master_trophy_dict(session):
    # This should probably be in a config file, but I'm not putting it
    # there just so it's a little less visible to casual perusal.
    izgc_trophy_list_url = "https://impzone.club/alltrophies.html"
    master_trophy_dict = {}

    # Could modularize this, but it's YAGNI for now
    response = session.get(izgc_trophy_list_url)
    soup = BeautifulSoup(response.text, "html.parser")

    trophies = soup.find_all("div", attrs={
        'class': re.compile('^item-trophy tooltip( plat)?')})
    for trophy in trophies:
        trophy_info_strings = tuple(trophy.stripped_strings)
        image_path = trophy.find('img')['src']
        game = trophy_info_strings[1]
        name = trophy_info_strings[0]
        trophy_data = {
            "full_name": f"[{game}] {name}",
            "game": game,
            "name": name,
            "system_year": trophy_info_strings[2]
        }
        master_trophy_dict[image_path] = trophy_data

    return master_trophy_dict


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
    def __init__(self, *, dispatcher):
        self.dispatcher = dispatcher
        super().__init__(
            dispatcher=dispatcher,
            thread_id=dispatcher.config["DEFAULT"]["izgc_thread_id"]
        )
        self.eligible_trophies = fb_handler.get_trophy_dict_from_db()

    def trophy_scan(self):
        imp_trophies = {}
        post_list = self.new_posts()

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
            for trophy_path, trophy_data in self.eligible_trophies.items():
                if re.search(trophy_path, image):
                    new_trophy = {trophy_data["game"]: {
                        trophy_data["name"]: {
                            "timestamp": post.timestamp(),
                            "link": post.link()
                        }}}
                    update_trophy_dict(earned_trophies, new_trophy)

        return earned_trophies
