# Sharded-Photos-Drive-CLI-Client

## Description

This project is the cli client of Sharded Photos Drive.

## Getting Started

## Getting Started to Contribute

1. Ensure Python3, Pip, and Poetry are installed on your machine

2. Install dependencies by running:

   ```bash
   poetry install
   ```

3. To lint your code, run:

   ```bash
   poetry run mypy . --check-untyped-defs && poetry run flake8 && poetry run black .
   ```

4. To run tests and code coverage, run:

   ```bash
   poetry run coverage run -m pytest && poetry run coverage report -m
   ```

5. To run tests and code coverage, run:

   ```bash
   poetry run coverage run -m pytest <insert-file-path> && poetry run coverage report -m
   ```

   For example,

   ```bash
   poetry run coverage run -m pytest tests/backup/test_backup_photos.py && poetry run coverage report -m
   ```

6. To publish a new version of the app:

   1. First, bump up the package version by running:

      ```bash
      poetry version [patch|minor|major]
      ```

      For instance, if the app is on 0.1.0 and you want to increment it to version 0.1.1, run:

      ```bash
      poetry version patch
      ```

   2. Then, create a pull request with the new version number.

   3. Once the pull request is submitted, go to <https://github.com/EKarton/Sharded-Photos-Drive/actions/workflows/publish-cli-client.yaml>, click on the `Run workflow`, ensure that it's on the `main` branch, and click on `Run workflow`:

      ![Screenshot of publish workflow](docs/images/publish-cli-client-screenshot.png)

   4. Once the action is complete, it will publish a new version of the app on <https://pypi.org/project/sharded_photos_drive_cli_client/>.

### Usage

Please note that this project is used for educational purposes and is not intended to be used commercially. We are not liable for any damages/changes done by this project.

### Credits

Emilio Kartono, who made the entire project.

### License

This project is protected under the GNU licence. Please refer to the root project's LICENSE.txt for more information.
