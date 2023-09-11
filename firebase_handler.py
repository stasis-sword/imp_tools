from datetime import datetime
import pytz

import firebase_admin
from firebase_admin import firestore
from firebase_admin import credentials
from google.cloud.firestore_v1.base_query import FieldFilter


class DbWarning(Warning):
    pass


class DbError(Exception):
    pass


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
                    "game": game,
                    "name": name,
                    'reference': trophy_doc.reference
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

    def get_imp_by_username(self, imp):
        imp_ref = self.db_client.document(f'imps/{imp}')
        imp_doc = imp_ref.get()
        if not imp_doc.exists:
            query = self.db_client.collection('imps').where(filter=FieldFilter(
                "currentUsername", "==", imp))
            imps_with_name = []
            for doc in query.stream():
                imps_with_name.append(doc)
            if len(imps_with_name) < 1:
                print(f'Warning: could not find {imp} in database.' +
                      ' If this is not a new club member, there ' +
                      'may be something wrong. Creating new record.')
                imp_ref.set({})
            elif len(imps_with_name) > 1:
                raise DbError(f'Imp lookup for {imp} failed! Multiple ' +
                              'records found with this as currentUsername.')
            else:
                imp_ref = imps_with_name[0].reference

        return imp_ref

    def write_trophies_to_db(self, imp, trophies):
        imp_ref = self.get_imp_by_username(imp)
        for game, trophy in trophies.items():
            for trophy_name, trophy_data in trophy.items():
                trophy_ref = self.db_client.document(
                    imp_ref.path +
                    f'/trophies{self.year}/[{game}] {trophy_name}'
                )
                trophy_ref.set({
                    'trophy': trophy_data['reference'],
                    'postUrl': trophy_data['link'],
                    'timestamp': datetime.strptime(
                        trophy_data['timestamp'], "%b %d, %Y %H:%M")
                })
