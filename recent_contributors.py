import datetime
import sys

from dispatcher import Dispatcher
from thread_reader import Thread


def by_time(user_post):
    return datetime.datetime.strptime(
        user_post[1].timestamp(), "%b %d, %Y %H:%M")


def get_sorted_recent_posts():
    posts = thread.new_posts()
    for post in posts:
        most_recent_posts[post.username] = post

    return sorted(most_recent_posts.items(), key=by_time, reverse=True)


dispatcher = Dispatcher()
dispatcher.login(required=False)

print("Preparing to scan thread for recent contributors.")
thread_id = input("Thread id: ")
thread = Thread(dispatcher=dispatcher, thread_id=thread_id)
print(f"Reading thread: {thread.name}")
confirm = input("Continue? (y/N)> ")
if confirm.lower() not in ["y", "yes"]:
    print("OK. Aborting.")
    sys.exit(0)

most_recent_posts = {}
sorted_recent_posts = get_sorted_recent_posts()

print("Most recent posts by each user (sorted by newest):")
for sorted_post in sorted_recent_posts:
    user = sorted_post[0]
    print(f"{user}: {most_recent_posts[user].timestamp()}")
