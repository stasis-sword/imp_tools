from datetime import datetime
import pytz

import firebase_admin
from firebase_admin import firestore
from firebase_admin import credentials


class FirebaseHandler:
    def __init__(self):
        cred = credentials.Certificate('service_account.json')
        firebase_admin.initialize_app(cred)
        self.db_client = firestore.client()
        # this could cause a problem if run right after the year ends...
        self.year = datetime.now().astimezone(pytz.timezone('US/Eastern')).year

    def get_firebase_trophies_by_collection_type(
            self, collection_name, year_property):
        trophy_dict = {}

        doc_stream = self.db_client.collection(collection_name).stream()
        for doc in doc_stream:
            properties = doc.to_dict()
            # only gather trophies from games/events from this year
            if properties[year_property] != self.year:
                continue

            path = doc.reference.path
            trophy_docs = self.db_client.collection(path + '/trophies')
            for trophy_doc in trophy_docs.stream():
                game = doc.id
                name = trophy_doc.id
                image_url = trophy_doc.to_dict()['imageUrl']
                trophy_data = {
                    'full_name': f"[{game}] {name}",
                    "game": game,
                    "name": name
                }
                trophy_dict[image_url] = trophy_data

        return trophy_dict

    def get_trophy_dict_from_db(self):
        game_trophies = self.get_firebase_trophies_by_collection_type(
            'games', 'clubYear')
        event_trophies = self.get_firebase_trophies_by_collection_type(
            'events', 'year')
        trophy_dict = game_trophies | event_trophies

        return trophy_dict

    def write_trophies_to_db(self):
        pass
