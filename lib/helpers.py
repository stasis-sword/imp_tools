import pytz


def use_single_thread_id_args(parser, default_thread_id):
    parser.add_argument(
        '--thread-id',
        metavar='{number}',
        type=int,
        default=default_thread_id,
        help='(optional) the numerical ID of the thread to check. If not ' +
             'supplied, defaults to IZGC thread.'
    )


def datetime_formatted_est(datetime):
    est = pytz.timezone('US/Eastern')
    as_est = datetime.astimezone(est).strftime("%b %d, %Y %H:%M") + ' EST'
    return as_est
