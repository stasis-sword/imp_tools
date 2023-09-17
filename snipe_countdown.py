import argparse

from lib.dispatcher import Dispatcher
from lib.thread_reader import Thread


parser = argparse.ArgumentParser(
    description='Count down posts to thread snipe.')
parser.add_argument(
    'thread_id', type=int, help='the numerical ID of the thread to check')


if __name__ == '__main__':
    args = parser.parse_args()
    dispatcher = Dispatcher()
    dispatcher.login(required=False)
    thread = Thread(dispatcher=dispatcher, thread_id=args.thread_id)

    sniper_countdown = thread.get_posts_left_til_snipe()
    print(f'Thread: {thread.name}')
    if sniper_countdown > 0:
        print(f'Posts left til snipe: {sniper_countdown}. Stay on target.')
    else:
        print("** Next post will snipe! **\nThere's no such thing as luck on" +
              ' the battlefield... be careful, Snake.')
