import re
import requests
import firebase_admin
from firebase_admin import firestore
from firebase_admin import credentials

from bs4 import BeautifulSoup

# requests
session = requests.Session()

# firebase
cred = credentials.Certificate('service_account.json')
app = firebase_admin.initialize_app(cred)
db = firestore.client()


def get_stripped_text(element):
    string_list = list(element.stripped_strings)
    text = ' '.join(string_list)
    return text


def get_trophy_dict():
    # This should probably be in a config file, but I'm not putting it
    # there just so it's a little less visible to casual perusal.
    izgc_trophy_list_url = "https://impzone.club/alltrophies.html"
    trophy_dict = {}

    # Could modularize this, but it's YAGNI for now
    response = session.get(izgc_trophy_list_url)
    soup = BeautifulSoup(response.text, "html.parser")

    trophies = soup.find_all("div", attrs={
        # skip trophies that end in "unique".
        # We can add those manually if we want.
        'class': re.compile('^item-trophy tooltip.*(?<!unique)$')})
    for trophy in trophies:
        trophy_info_spans = list(
            map(get_stripped_text, trophy.find_all("span")))
        image_path = trophy.find('img')['src']
        system_year = trophy_info_spans[2]
        name = trophy_info_spans[0]

        plat = "PLATINUM" in name
        if "SECRET" not in name:
            secret = {}
            game = trophy_info_spans[1]
        else:
            game = ""
            secret = {"description": trophy_info_spans[1]}
            if "2022" in system_year:
                secret["year"] = 2022
            elif "2023" in system_year:
                secret["year"] = 2023
            else:
                continue

        # replace badly parsed apostrophe character
        game = game.replace('â\x80\x99', "’")
        name = name.replace('â\x80\x99', "’")

        trophy_data = {
            "image_url": image_path,
            "game": game,
            "name": name,
            "plat": plat,
            "secret": secret
        }
        trophy_dict[image_path] = trophy_data

    return trophy_dict


def add_new_trophy(image_url, game, name, plat, secret):
    game_alt_display_name = False
    if "/" in game:
        game_alt_display_name = game
        game = game.replace("/", " ")
    trophy_data = {"imageUrl": image_url}

    if "/" in name:
        trophy_data["altDisplayName"] = name
        name = name.replace("/", " ")

    if plat:
        trophy_data["plat"] = True

    if secret:
        collection = "events"
        game_or_event = f"Secret Trophies {secret['year']}"
        trophy_data["description"] = secret["description"]
        trophy_data["secret"] = True
    else:
        collection = "games"
        game_or_event = game
        game_doc = db.collection("games").document(game).get()
        if not game_doc.exists:
            print(f"creating new game: {game}")
            game_data = {"clubYear": 2023}
            if game_alt_display_name:
                game_data["altDisplayName"] = game_alt_display_name
            db.collection("games").document(game).set(game_data)

    print(f"creating new trophy: {name}")
    db.collection(
        collection, game_or_event, "trophies"
    ).document(name).set(trophy_data)


if __name__ == "__main__":
    dicty = get_trophy_dict()
    for new_trophy in dicty.items():
        add_new_trophy(**new_trophy[1])
