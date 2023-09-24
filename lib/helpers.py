def use_single_thread_id_args(parser, default_thread_id):
    parser.add_argument(
        '--thread-id',
        metavar='{number}',
        type=int,
        default=default_thread_id,
        help='(optional) the numerical ID of the thread to check. If not ' +
             'supplied, defaults to IZGC thread.'
    )
