import unittest
import logging
import sys
from io import StringIO
from contextlib import contextmanager

from sharded_photos_drive_cli_client.cli.shared.logging import setup_logging


class TestSetupLogging(unittest.TestCase):

    @contextmanager
    def captured_output(self):
        new_out, new_err = StringIO(), StringIO()
        old_out, old_err = sys.stdout, sys.stderr
        try:
            sys.stdout, sys.stderr = new_out, new_err
            yield sys.stdout, sys.stderr
        finally:
            sys.stdout, sys.stderr = old_out, old_err

    def setUp(self):
        # Reset the logging configuration before each test
        logging.root.handlers = []

    def test_verbose_logging(self):
        setup_logging(is_verbose=True)

        self.assertEqual(logging.getLogger().level, logging.DEBUG)
        self.assertTrue(
            any(
                isinstance(handler, logging.StreamHandler)
                and handler.stream == sys.stdout
                for handler in logging.getLogger().handlers
            )
        )

    def test_non_verbose_logging(self):
        setup_logging(is_verbose=False)

        self.assertEqual(logging.getLogger().level, logging.INFO)
        self.assertTrue(
            any(
                isinstance(handler, logging.StreamHandler)
                and handler.stream == sys.stdout
                for handler in logging.getLogger().handlers
            )
        )

    def test_log_output_verbose(self):
        with self.captured_output() as (out, _):
            setup_logging(is_verbose=True)
            logging.debug("This is a debug message")
            logging.info("This is an info message")

        output = out.getvalue().strip()
        self.assertIn("This is a debug message", output)
        self.assertIn("This is an info message", output)

    def test_log_output_non_verbose(self):
        with self.captured_output() as (out, _):
            setup_logging(is_verbose=False)
            logging.debug("This is a debug message")
            logging.info("This is an info message")

        output = out.getvalue().strip()
        self.assertNotIn("This is a debug message", output)
        self.assertIn("This is an info message", output)
