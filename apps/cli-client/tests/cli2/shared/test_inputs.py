from io import StringIO
import unittest
from unittest.mock import Mock, patch
from pymongo import MongoClient

from sharded_photos_drive_cli_client.cli2.shared.inputs import (
    prompt_user_for_mongodb_connection_string,
    prompt_user_for_non_empty_input_string,
    prompt_user_for_non_empty_password,
    prompt_user_for_yes_no_answer,
)
from sharded_photos_drive_cli_client.shared.metadata.testing.mock_mongo_client import (
    create_mock_mongo_client,
)


class TestPromptUserForMongodbConnectionString(unittest.TestCase):
    def tearDown(self):
        patch.stopall()

    def test_valid_connection_string(self):
        # Test setup: mock MongoClient
        mongodb_client = create_mock_mongo_client()
        patch.object(MongoClient, '__init__', return_value=None).start()
        patch.object(MongoClient, '__new__', return_value=mongodb_client).start()

        # Test setup: mock getpass
        mock_get_pass = patch('getpass.getpass').start()
        mock_get_pass.return_value = 'mongodb://localhost:8080'

        # Act: call the function
        output = prompt_user_for_mongodb_connection_string('Enter connection string')

        # Assert: check on output
        self.assertEqual(output, 'mongodb://localhost:8080')

    def test_invalid_connection_string(self):
        # Test setup: mock MongoClient
        incorrect_mongodb_client = Mock()
        incorrect_mongodb_client.admin.command.side_effect = ValueError(
            "Custom error message"
        )
        correct_mongodb_client = create_mock_mongo_client()

        patch.object(MongoClient, '__init__', return_value=None).start()
        patch.object(MongoClient, '__new__').start().side_effect = [
            incorrect_mongodb_client,
            correct_mongodb_client,
        ]

        # Test setup: mock getpass
        mock_get_pass = patch('getpass.getpass').start()
        mock_get_pass.side_effect = [
            'mongodb://localhost:8080',
            'mongodb://localhost:9090',
        ]

        # Act: call the function
        output = prompt_user_for_mongodb_connection_string('Enter connection string')

        # Assert: check on output
        self.assertEqual(output, 'mongodb://localhost:9090')


class TestPromptUserForNonEmptyPassword(unittest.TestCase):

    @patch('getpass.getpass')
    def test_valid_password(self, mock_getpass):
        mock_getpass.return_value = "valid_password"
        result = prompt_user_for_non_empty_password("Enter password: ")
        self.assertEqual(result, "valid_password")

    @patch('getpass.getpass')
    def test_empty_then_valid_password(self, mock_getpass):
        mock_getpass.side_effect = ["", "valid_password"]
        with patch('builtins.print') as mock_print:
            result = prompt_user_for_non_empty_password("Enter password: ")
            self.assertEqual(result, "valid_password")
            mock_print.assert_called_once_with(
                "Input cannot be empty. Please try again."
            )

    @patch('getpass.getpass')
    def test_whitespace_then_valid_password(self, mock_getpass):
        mock_getpass.side_effect = ["   ", "valid_password"]
        result = prompt_user_for_non_empty_password("Enter password: ")
        self.assertEqual(result, "valid_password")

    @patch('getpass.getpass')
    def test_custom_prompt(self, mock_getpass):
        mock_getpass.return_value = "secret123"
        custom_prompt = "Enter your secret password: "
        result = prompt_user_for_non_empty_password(custom_prompt)
        self.assertEqual(result, "secret123")
        mock_getpass.assert_called_once_with(custom_prompt)


class TestPromptUserForNonEmptyInputString(unittest.TestCase):

    @patch('builtins.input', return_value='valid_input')
    def test_valid_input(self, mock_input):
        result = prompt_user_for_non_empty_input_string("Enter input: ")

        self.assertEqual(result, 'valid_input')
        mock_input.assert_called_once_with("Enter input: ")

    @patch('builtins.input', side_effect=['', '   ', 'valid_input'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_empty_and_whitespace_inputs(self, mock_stdout, mock_input):
        result = prompt_user_for_non_empty_input_string("Enter input: ")

        self.assertEqual(result, 'valid_input')
        self.assertEqual(mock_input.call_count, 3)
        self.assertEqual(
            mock_stdout.getvalue(), "Input cannot be empty. Please try again.\n" * 2
        )

    @patch('builtins.input', return_value='  spaced_input  ')
    def test_input_with_leading_and_trailing_spaces(self, mock_input):
        result = prompt_user_for_non_empty_input_string("Enter input: ")

        self.assertEqual(result, 'spaced_input')


class TestPromptUserForYesNoAnswer(unittest.TestCase):

    @patch('builtins.input')
    def test_yes_inputs(self, mock_input):
        yes_inputs = ['yes', 'YES', 'y', 'Y', '  Yes  ', ' y ']
        for yes_input in yes_inputs:
            mock_input.return_value = yes_input
            result = prompt_user_for_yes_no_answer("Do you agree? ")

            self.assertTrue(result)

    @patch('builtins.input')
    def test_no_inputs(self, mock_input):
        no_inputs = ['no', 'NO', 'n', 'N', '  No  ', ' n ']
        for no_input in no_inputs:
            mock_input.return_value = no_input
            result = prompt_user_for_yes_no_answer("Do you agree? ")

            self.assertFalse(result)

    @patch('builtins.input', side_effect=['invalid', 'yes'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_invalid_then_valid_input(self, mock_stdout, mock_input):
        result = prompt_user_for_yes_no_answer("Do you agree? ")

        self.assertTrue(result)
        self.assertEqual(mock_input.call_count, 2)
        self.assertEqual(
            mock_stdout.getvalue(), "Invalid input. Please enter 'y' or 'n'\n"
        )

    @patch('builtins.input', side_effect=['maybe', 'nope', 'n'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_multiple_invalid_inputs(self, mock_stdout, mock_input):
        result = prompt_user_for_yes_no_answer("Do you agree? ")

        self.assertFalse(result)
        self.assertEqual(mock_input.call_count, 3)
        self.assertEqual(
            mock_stdout.getvalue(), "Invalid input. Please enter 'y' or 'n'\n" * 2
        )
