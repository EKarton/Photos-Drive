# Sharded-Photos-Drive-CLI-Client

![PyPI - Version](https://img.shields.io/pypi/v/sharded_photos_drive_cli_client)
![check-code-coverage](https://img.shields.io/badge/code--coverage-99-brightgreen)

## Description

The Sharded-Photos-Drive-CLI-Client is the cli client for Sharded Photos Drive. This CLI helps set up your infrastructure, syncs, adds, and delete your pictures and videos from your machine to Sharded Photos Drive.

This CLI will never delete content from your machine - it should only mirror the content from your machine to the cloud.

## Table of Contents

- [Getting Started](#getting-started)
  - [Installation](#installation)
  - [Setting up your infrastructure](#setting-up-your-infrastructure)
  - [Syncing your photos / videos](#syncing-your-photos--videos)
  - [Adding custom content](#adding-custom-content-to-sharded-photos-drive)
  - [Deleting custom content](#deleting-content-to-sharded-photos-drive)
  - [Cleaning](#cleaning-trailing-sharded-photos-drive)
  - [Deleting everything](#deleting-all-content-in-sharded-photos-drive)
- [Getting Started to Contribute](#getting-started-to-contribute)
- [Usage](#usage)
- [Credits](#credits)
- [License](#license)

## Getting Started

### Installation

1. First, install a tool called [Exiftool](https://exiftool.org/)
   - It's a tool used to parse through exif metadata in your photos / videos.

2. Second, install this Python package by running:

   ```bash
   pip3 install sharded_photos_drive_cli_client
   ```

### Setting up your infrastructure

1. First, you need to have the following:

   1. A connection string to your MongoDB database (follow [this doc](./docs/create_mongodb_connection_string.md) for step-by-step instructions).
   2. Your Google Account's client ID and client secrets (follow [this doc](./docs/create_google_client_id.md) for step-by-step instructions).

2. Next, to set up your infrastructure by running `sharded_photos_drive_cli_client config init`.

3. It will ask you information on what the command will do.

   ![Intro](./docs/images/setting-up-infra/intro.png)

   Press `[enter]` to continue.

4. Next, the cli will prompt you to specify a place to store the configs. You can store it locally or on MongoDB.

   For simplicity, select `2`. It will then ask you to enter the file name of your config.

   ![Config choices](./docs/images/setting-up-infra/config-choices.png)

5. Next, it will ask you to add a MongoDB database to store your pictures / videos metadata. It will prompt you to enter a name for your database, and its read-write connection string:

   ![Adding MongoDB client](./docs/images/setting-up-infra/add-mongodb.png)

6. Finally, it will ask you to add your Google Photos account to store your pictures / videos. It will prompt you to enter a name for your first Google Photos account, and a Google Photos Client ID and Google Photos Client Secret.

   ![Adding Google Photos account](./docs/images/setting-up-infra/add-gphotos.png)

7. After specifying the name, client ID, and client secret, it will return a URL to authenticate. Copy-paste the URL to your browser and follow the instructions on the browser:

   ![Google OAuth2 steps](./docs/images/setting-up-infra/google-oauth2.gif)

8. It saves the config to `my-config.conf` to your current working directory.

### Syncing your photos / videos

1. From the previous step, assume you have `config.conf` as your config file, and assume your current working directory looks like this:

   ```bash
   .
   ├── Archives
   │   ├── Photos
   │   │   ├── 2023
   │   │   │   └── Wallpapers
   │   │   │       └── 2023-11a Wallpaper.DNG
   │   │   └── 2024
   │   │       └── Wallpapers
   │   │           ├── 2024-01a Wallpaper.jpg
   │   │           ├── 2024-03-01 Wallpaper.jpg
   │   │           ├── 2024-04-02 Wallpaper.DNG
   │   │           └── 2024-05 Wallpaper.png
   │   └── Random.jpg
   └── my-config.conf
   ```

2. To sync your photos / videos to the system, run:

   ```bash
   sharded_photos_drive_cli sync --local_dir_path . --config_file config.conf
   ```

3. It will then ask you to confirm if these are the contents that you want to upload to the system. Type in `yes`:

   ![Diff](./docs/images/syncing/diff.png)

4. After a while, the contents should be uploaded and will output statistics on the upload.

   ![Stats](./docs/images/syncing/sync-stats.png)

5. If you want to sync your photos/videos in a particular path in the system, you can specify the `--remote_albums_path` field, like:

   ```bash
   sharded_photos_drive_cli sync --local_dir_path ./Archives --remote_albums_path Archives  --config_file config.conf
   ```

   It will compare all contents under the local directory `./Archives` to all content under the albums path `Archives`.

6. You can also upload photos / videos in parallel with the `--parallelize_uploads` flag, like:

   ```bash
   sharded_photos_drive_cli sync --local_dir_path . --config_file config.conf --parallelize_uploads
   ```

   though it is experimental right now.

### Adding custom content to Sharded Photos Drive

1. Suppose your Sharded Photos Drive has the following content:

   ```bash
   root
   └── Archives
       ├── Photos
       │   └── 2024
       │       └── Wallpapers
       │           ├── 2024-01a Wallpaper.jpg
       │           ├── 2024-03-01 Wallpaper.jpg
       │           ├── 2024-04-02 Wallpaper.DNG
       │           └── 2024-05 Wallpaper.png
       └── Random.jpg
   ```

   and you want to upload the current content in your working directory:

   ```bash
   .
   └── Current
       └── Dog.jpg
   ```

2. You can run:

   ```bash
   sharded_photos_drive_cli add ./Current --config_file my-config.conf
   ```

   and your system will add all contents under `./Current` without deleting any existing content in your system.

3. In other words, you will have these contents:

   ```bash
   root
   ├── Archives
   │   ├── Photos
   │   │   └── 2024
   │   │       └── Wallpapers
   │   │           ├── 2024-01a Wallpaper.jpg
   │   │           ├── 2024-03-01 Wallpaper.jpg
   │   │           ├── 2024-04-02 Wallpaper.DNG
   │   │           ├── 2024-05 Wallpaper.png
   │   └── Random.jpg
   └── Current
       └── Dog.jpg
   ```

### Deleting content to Sharded Photos Drive

1. Similarly, if your system has this content:

   ```bash
   root
   └── Archives
       ├── Photos
       │   └── 2024
       │       └── Wallpapers
       │           ├── 2024-01a Wallpaper.jpg
       │           ├── 2024-03-01 Wallpaper.jpg
       │           ├── 2024-04-02 Wallpaper.DNG
       │           ├── 2024-05 Wallpaper.png
       └── Random.jpg
   ```

2. If you want to delete the `Archives/Random.jpg` picture, you can run:

   ```bash
   sharded_photos_drive_cli delete Archives/Random.jpg --config_file my-config.conf
   ```

   and the photo `Archives/Random.jpg` will be deleted from the system.

3. Similarly, if you want to delete everything under the `Archives/Photos` album, you can run:

   ```bash
   sharded_photos_drive_cli delete Archives/Photos --config_file my-config.conf
   ```

   and the system will have these new contents:

   ```bash
   root
   └── Archives
       └── Random.jpg
   ```

### Cleaning trailing Sharded Photos Drive

In case any of the `sync`, `add`, or `delete` commands fail, there are data that can be cleaned up. Moreover, when a photo / video is deleted, due to the limitations of the Google Photos API, it will remain in your Google Photos account.

Hence, the `clean` script is provided to clean up the system.

Running:

```bash
sharded_photos_drive_cli clean --config_file config.conf
```

will:

1. Delete all media items from the metadata database that is not being used
2. Delete all albums from the metadata database that is not being used
3. Move photos / videos in Google Photos that are not used to a special album called `To delete` where you can manually delete the content in your Google Photos account.

### Deleting all content in Sharded Photos Drive

In case you want to delete everything, you can run:

```bash
sharded_photos_drive_cli teardown --config_file config.conf
```

It will delete all photos / videos from your system, and move all photos / videos in your Google Photo accounts to their `To delete` albums.

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

      ![Screenshot of publish workflow](docs/images/publish-package/publish-cli-client-screenshot.png)

   4. Once the action is complete, it will publish a new version of the app on <https://pypi.org/project/sharded_photos_drive_cli_client/>.

## Usage

Please note that this project is used for educational purposes and is not intended to be used commercially. We are not liable for any damages/changes done by this project.

## Credits

Emilio Kartono, who made the entire project.

CLI images were provided by <https://ray.so/>.

## License

This project is protected under the GNU licence. Please refer to the root project's LICENSE.txt for more information.
