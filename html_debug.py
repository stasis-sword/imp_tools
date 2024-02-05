import argparse
import pickle

from lib.dispatcher import Dispatcher
from lib.thread_reader import Thread
from lib.helpers import use_single_thread_id_args

dispatcher = Dispatcher()

parser = argparse.ArgumentParser(
    description='Spit out beautifulsoup debug info for thread page.')
use_single_thread_id_args(parser, dispatcher.default_thread)

if __name__ == '__main__':
    args = parser.parse_args()

    dispatcher.login(required=False)
    thread = Thread(dispatcher=dispatcher, thread_id=args.thread_id)

    last_page = thread.get_last_page_number()
    raw_page = thread.get_raw_page(last_page)

    with open("debug_data.pkl", "wb") as file:
        pickle.dump(raw_page, file, pickle.HIGHEST_PROTOCOL)
