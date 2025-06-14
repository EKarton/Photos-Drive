import logging
import sys


def setup_logging(is_verbose: bool):
    '''
    Sets up logging.

    Args:
        is_verbose (bool): Whether to show all debug output or not.
    '''
    if is_verbose:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    else:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
