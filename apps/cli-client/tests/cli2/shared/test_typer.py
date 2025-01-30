from typing_extensions import Annotated
import unittest
import typer
from typer.testing import CliRunner

from sharded_photos_drive_cli_client.cli2.shared.typer import (
    createMutuallyExclusiveGroup,
)


class TestMutuallyExclusiveGroup(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.app = typer.Typer()
        self.callback = createMutuallyExclusiveGroup(2)

        @self.app.command()
        def cmd(
            param1: Annotated[str | None, typer.Option(callback=self.callback)] = None,
            param2: Annotated[str | None, typer.Option(callback=self.callback)] = None,
        ):
            typer.echo(f"Param1: {param1}, Param2: {param2}")

    def test_no_conflict(self):
        result = self.runner.invoke(self.app, ["--param1", "value1"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Param1: value1, Param2: None", result.stdout)

    def test_conflict(self):
        result = self.runner.invoke(
            self.app, ["--param1", "value1", "--param2", "value2"]
        )

        self.assertEqual(result.exit_code, 2)
        self.assertIn("param2 is mutually exclusive with", result.stdout)
