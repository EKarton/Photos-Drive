# Photos-Drive-CLI-Client

![PyPI - Version](https://img.shields.io/pypi/v/photos_drive)
![check-code-coverage](https://img.shields.io/badge/code--coverage-99-brightgreen)

## Description

The Photos-Drive-CLI-Client is the cli client for Photos Drive. This CLI helps set up your infrastructure, syncs, adds, and delete your pictures and videos from your machine to Photos Drive.

This CLI will never delete content from your machine - it should only mirror the content from your machine to the cloud.

## Table of Contents

- [Getting Started](#getting-started)
- [Getting Started to Contribute](#getting-started-to-contribute)
- [Usage](#usage)
- [Credits](#credits)
- [License](#license)

## Getting Started

Refer to [this doc](./docs/getting_started.md) on step-by-step instructions on how to get started with the Photos Drive CLI.

## Getting Started to Contribute

1. Ensure Python3, Pip, and Poetry are installed on your machine

1. Install dependencies by running:

   ```bash
   poetry install
   ```

1. To lint your code, run:

   ```bash
   poetry run mypy . && poetry run flake8 && poetry run isort . && poetry run black .
   ```

1. To run all tests and code coverage, run:

   ```bash
   poetry run coverage run  --source=photos_drive -m pytest tests/ && poetry run coverage report -m
   ```

1. To run tests and code coverage for a particular test file, run:

   ```bash
   poetry run coverage run --source=photos_drive -m pytest <insert-file-path> && poetry run coverage report -m
   ```

   For example,

   ```bash
   poetry run coverage run --source=photos_drive -m pytest tests/backup/test_backup_photos.py && poetry run coverage report -m
   ```

1. To publish a new version of the app:

   1. First, bump up the package version by running:

      ```bash
      poetry version [patch|minor|major]
      ```

      For instance, if the app is on 0.1.0 and you want to increment it to version 0.1.1, run:

      ```bash
      poetry version patch
      ```

   1. Then, create a pull request with the new version number.

   1. Once the pull request is submitted, it will publish a new version of the app on <https://pypi.org/project/photos_drive_cli_client/>.

## Usage

Please note that this project is used for educational purposes and is not intended to be used commercially. We are not liable for any damages/changes done by this project.

## Credits

Emilio Kartono, who made the entire project.

CLI images were provided by <https://ray.so/> in Ice theme.

## License

This project is protected under the GNU licence. Please refer to the root project's LICENSE.txt for more information.
