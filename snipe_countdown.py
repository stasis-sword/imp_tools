import sys

from lib.dispatcher import Dispatcher
from lib.thread_reader import Thread
from lib.imp_tool_errors import InvalidArgumentError

USAGE_MESSAGE = "Usage: snipe_countdown {thread id}. ID should be a number."

try:
    thread_id = int(sys.argv[1])
except IndexError as exc:
    raise InvalidArgumentError(
        f"No thread id supplied.\n{USAGE_MESSAGE}") from exc
except ValueError as exc:
    raise InvalidArgumentError(
        f"Invalid thread id supplied.\n{USAGE_MESSAGE}") from exc

dispatcher = Dispatcher()
dispatcher.login(required=False)
thread = Thread(dispatcher=dispatcher, thread_id=thread_id)

sniper_countdown = thread.get_posts_left_til_snipe()
print(f'Thread: {thread.name}')
if sniper_countdown > 0:
    print(f'Posts left til snipe: {sniper_countdown}. Stay on target.')
else:
    print("** Next post will snipe! **\nThere's no such thing as luck on the" +
          ' battlefield... be careful, Snake.')
