import sys

from lib.dispatcher import Dispatcher
from lib.trophy_scanner import TrophyReporter, IZGCThread
from lib.imp_tool_errors import InvalidArgumentError

USAGE_MESSAGE = "Usage: read_izgc_trophies --start-page {page number}"

# Accept command line overrides for all pages or starting page
if len(sys.argv) > 1:
    if sys.argv[1] == "--start-page":
        try:
            override_page = int(sys.argv[2])
        except IndexError as exc:
            raise InvalidArgumentError(
                f"No page number supplied.\n{USAGE_MESSAGE}") from exc
        except ValueError as exc:
            raise InvalidArgumentError(
                f"Invalid page number supplied.\n{USAGE_MESSAGE}") from exc

    if "--all-pages" in sys.argv:
        override_page = 1
    else:
        override_page = False
else:
    override_page = False

dispatcher = Dispatcher()
dispatcher.login(required=False)
club_thread = IZGCThread(dispatcher=dispatcher)

if override_page:
    club_thread.page_number = override_page
    club_thread.last_post = 0
else:
    club_thread.load_previous_stopping_point()

if len(sys.argv) > 1:
    if sys.argv[1] == "--start-page":
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
