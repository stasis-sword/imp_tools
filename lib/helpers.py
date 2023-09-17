def use_single_thread_id_args(parser):
    parser.add_argument(
        'thread_id',
        metavar='thread ID',
        type=int,
        help='the numerical ID of the thread to check'
    )
