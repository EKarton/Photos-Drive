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

5. To publish your app:

   1. First, set your PyPI api token to Poetry

      ```bash
      poetry config pypi-token.pypi <YOUR_API_TOKEN>
      ```

   2. Then, build the app by running:

      ```bash
      poetry build
      ```

   3. Finally, publish the app by running:

      ```bash
      poetry publish
      ```

### Usage

Please note that this project is used for educational purposes and is not intended to be used commercially. We are not liable for any damages/changes done by this project.

### Credits

Emilio Kartono, who made the entire project.

### License

This project is protected under the GNU licence. Please refer to the LICENSE.txt for more information.
