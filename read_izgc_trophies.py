import sys

from dispatcher import Dispatcher
from trophy_scanner import TrophyReporter, IZGCThread

dispatcher = Dispatcher()
dispatcher.login(required=False)
club_thread = IZGCThread(dispatcher=dispatcher)


class InvalidArgumentError(Exception):
    pass


# Accept command line argument to read all pages
if "--all-pages" not in sys.argv:
    club_thread.load_previous_stopping_point()
if len(sys.argv) > 1:
    if sys.argv[1] == "--start-page":
        USAGE_MESSAGE = "Usage: read_izgc_trophies --start-page {page number}"
        try:
            club_thread.page_number = int(sys.argv[2])
            club_thread.last_post = 0
        except IndexError as exc:
            raise InvalidArgumentError(
                f"No page number supplied.\n{USAGE_MESSAGE}") from exc
        except ValueError as exc:
            raise InvalidArgumentError(
                f"Invalid page number supplied.\n{USAGE_MESSAGE}") from exc

imp_trophies = club_thread.trophy_scan()
reporter = TrophyReporter(imp_trophies)
reporter.report_new_trophies()
