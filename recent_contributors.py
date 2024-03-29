import argparse

from lib.dispatcher import Dispatcher
from lib.thread_reader import Thread
from lib.helpers import use_single_thread_id_args, datetime_formatted_est


def by_time(user_post):
    return user_post[1].timestamp


def get_sorted_recent_posts():
    posts = thread.new_posts()
    for post in posts:
        most_recent_posts[post.username] = post

    return sorted(most_recent_posts.items(), key=by_time, reverse=True)


dispatcher = Dispatcher()

parser = argparse.ArgumentParser(
    description=('get a list of recent contributors to a thread, and the ' +
                 'timestamp of their most recent post.')
)
use_single_thread_id_args(parser, dispatcher.default_thread)

if __name__ == '__main__':
    args = parser.parse_args()

    dispatcher.login(required=False)

    print("Preparing to scan thread for recent contributors.")
    thread = Thread(dispatcher=dispatcher, thread_id=args.thread_id)
    print(f"Reading thread: {thread.name}")
    confirm = input("This may take a few minutes. Continue? (y/N)> ")
    if confirm.lower() not in ["y", "yes"]:
        print("OK. Aborting.")
    else:
        most_recent_posts = {}
        sorted_recent_posts = get_sorted_recent_posts()

        print("Most recent posts by each user (sorted by newest):")
        for sorted_post in sorted_recent_posts:
            user = sorted_post[0]
            formatted_timestamp = datetime_formatted_est(
                most_recent_posts[user].timestamp)
            print(f"{user}: {formatted_timestamp}")
