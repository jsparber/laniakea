# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2022 Matthias Klumpp <matthias@tenstral.net>
#
# SPDX-License-Identifier: LGPL-3.0+

import sys
from argparse import ArgumentParser

__mainfile = None


def run_server(options):
    from laniakea.localconfig import LocalConfig
    from lkscheduler.scheduler_daemon import SchedulerDaemon

    if options.config_fname:
        LocalConfig(options.config_fname)

    if options.verbose:
        from laniakea.logging import set_verbose

        set_verbose(True)

    daemon = SchedulerDaemon()
    daemon.run()


def check_print_version(options):
    if options.show_version:
        from laniakea import __version__

        print(__version__)
        sys.exit(0)


def create_parser():
    '''Create Laniakea Scheduler CLI argument parser'''

    parser = ArgumentParser(description='Archive management task scheduler')

    # generic arguments
    parser.add_argument('--verbose', action='store_true', dest='verbose', help='Enable debug messages.')
    parser.add_argument(
        '--version', action='store_true', dest='show_version', help='Display the version of Laniakea itself.'
    )
    parser.add_argument(
        '--config',
        action='store',
        dest='config_fname',
        default=None,
        help='Location of the base configuration file to use.',
    )

    parser.set_defaults(func=run_server)

    return parser


def run(mainfile, args):
    global __mainfile
    __mainfile = mainfile

    parser = create_parser()

    args = parser.parse_args(args)
    check_print_version(args)
    args.func(args)
