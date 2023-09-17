import argparse

from lib.dispatcher import Dispatcher
from lib.trophy_scanner import TrophyReporter, IZGCThread


parser = argparse.ArgumentParser(
    description=(
            'Read new trophies from the IZGC thread. Reports new trophies on' +
            ' the command line, saves to trophy_timestamps.json, and uploads' +
            ' to remote db'))
parser.add_argument(
    '--start-page',
    metavar='{page number}',
    type=int,
    help='(optional) page to start scanning on')
parser.add_argument(
    '--all-pages',
    action='store_true',
    help=('if called, start at the beginning of the thread. overrides ' +
          '--start-page.')
)


if __name__ == '__main__':
    args = parser.parse_args()

    dispatcher = Dispatcher()
    dispatcher.login(required=False)
    club_thread = IZGCThread(dispatcher=dispatcher)

    if args.all_pages:
        club_thread.page_number = 1
        club_thread.last_post = 0
    elif args.start_page:
        club_thread.page_number = 1
        club_thread.last_post = 0
    else:
        club_thread.load_previous_stopping_point()

    imp_trophies = club_thread.trophy_scan()
    reporter = TrophyReporter(imp_trophies)
    reporter.report_new_trophies()
