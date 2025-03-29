from datetime import datetime
import os
from pathlib import Path

import pytz
import firebase_admin
from firebase_admin import firestore
from firebase_admin import credentials
from google.cloud.firestore_v1.base_query import FieldFilter

CLUB_TIMEZONE = pytz.timezone('US/Eastern')


class DbWarning(Warning):
    pass


class DbError(Exception):
    pass


def new_year_datetime(year):
    naive = datetime(year, 1, 1)
    localized = CLUB_TIMEZONE.localize(naive)
    utc = localized.astimezone(pytz.timezone('utc'))
    return utc


class FirebaseHandler:
    def __init__(self, year=None):
        # Check if we're in a Cloud Function environment
        if os.getenv('FUNCTION_TARGET'):
            # Use default credentials in Cloud Functions
            cred = credentials.ApplicationDefault()
        else:
            # Look for service_account.json in the imp_tools root directory
            current_dir = Path(__file__).parent.parent
            service_account_path = current_dir / 'service_account.json'
            if not service_account_path.exists():
                raise FileNotFoundError(
                    f"Service account file not found at {service_account_path}\n"
                    "Please ensure service_account.json is in the imp_tools root directory"
                )
            cred = credentials.Certificate(str(service_account_path))
            firebase_admin.initialize_app(cred)
        
        self.db_client = firestore.client()
        self.year = year or datetime.now().astimezone(CLUB_TIMEZONE).year
        self.all_trophies_event_windows = []
        self._eligible_trophies = None

    @property
    def eligible_trophies(self):
        if self._eligible_trophies is None:
            self._eligible_trophies = self.get_trophy_dict_from_db()

        return self._eligible_trophies

    def get_time_window(self, game_or_event_doc):
        properties = game_or_event_doc.to_dict()
        default_start_time = new_year_datetime(self.year)
        default_end_time = new_year_datetime(self.year + 1)

        if properties.get('startTime') and properties.get('endTime'):
            start_time = properties['startTime']
            end_time = properties['endTime']
            # if event is open for all trophies (e.g. Impmas) add it to list of
            # all trophy time windows
            if properties.get('allTrophiesEvent'):
                window = {'start_time': start_time, 'end_time': end_time}
                self.all_trophies_event_windows.append(window)
            return start_time, end_time

        # game or event doesn't have a time window set. Check for umbrella
        # event with time window
        if not properties.get('event'):
            print(f'*** Warning! {game_or_event_doc.id} has no start ' +
                  'and/or end time and no associated umbrella event. No ' +
                  'time window will be applied for its trophies.')
            return default_start_time, default_end_time

        event_doc = properties['event'].get()
        event = event_doc.to_dict()
        if event.get('startTime') and event.get('endTime'):
            start_time = event['startTime']
            end_time = event['endTime']
            return start_time, end_time

        print(f'*** Warning! {game_or_event_doc.id} is associated ' +
              f'with event {event.id}, which does not have a start ' +
              'and/or end time. No time window will be applied for ' +
              'its trophies.')
        return default_start_time, default_end_time

    def get_firebase_trophies_by_collection_type(
            self, collection_name, year_property):
        trophy_dict = {}

        doc_stream = self.db_client.collection(collection_name).stream()
        for doc in doc_stream:
            properties = doc.to_dict()
            # don't scan for trophies from hidden games/events
            if properties.get('hidden'):
                continue

            # only gather trophies from games/events from this year
            doc_year = properties.get(year_property)
            if not doc_year:
                print(f'*** Warning! No year entered for {doc.id}. Trophies ' +
                      'will never be gathered.')
                continue
            if doc_year != self.year:
                continue

            start_time, end_time = self.get_time_window(doc)

            path = doc.reference.path
            trophy_docs = self.db_client.collection(path + '/trophies')
            for trophy_doc in trophy_docs.stream():
                trophy_data = {
                    "game": doc.id,
                    "name": trophy_doc.id,
                    'reference': trophy_doc.reference,
                    "start_time": start_time,
                    "end_time": end_time
                }
                image_url = trophy_doc.to_dict()['imageUrl']
                trophy_dict[image_url] = trophy_data

        return trophy_dict

    def get_trophy_dict_from_db(self):
        print('Retrieving eligible trophies from db...')
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
                    'timestamp': trophy_data['timestamp'],
                })
