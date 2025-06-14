# Photos Drive

[![Netlify Status](https://api.netlify.com/api/v1/badges/36282e46-c4ab-407f-8a6e-b6dbb4f40748/deploy-status)](https://app.netlify.com/projects/photosdrive-demo/deploys)

Photos Drive is a unified photo management platform designed to connect and display all your photos across different photo storage solutions in one place.

It syncs and uploads photos from your computer to configured databases and photo storage accounts using a CLI tool. A web UI then presents your photos in a list or map view, organized by nested albums that reflect the folder structure on your computer.

## Architecture Overview

The system consists of three main applications:

1. **[CLI Client](./apps/cli-client/README.md)**
   A Python library and CLI tool that enables users to back up photos from their computer to the system.

2. **[Web API](./apps/web-api/README.md)**
   Reads photo metadata from MongoDB and serves it to the Web UI via REST endpoints.

3. **[Web UI](./apps/web-ui/README.md)**
   A frontend application that fetches albums and photos from the Web API to display them to users in the browser.

## Technology Stack

* **Photo metadata storage:** MongoDB
* **Photo blob storage:** Google Photos
* **Authentication:** Google OAuth2 (between Web UI and Web API)
* **Access control:** Allow list configured via environment variables (future plans include multi-user ACLs)

## Databases

There are two types of databases in the system:

### 1. Config Database

Stores credentials and configuration details for metadata databases and photo storage accounts. Refer to [this guide](./docs/database_schema.md) for more info on their schemas.

* **Root Album table**
  Contains exactly one row, which points to the root album location.

* **Google Photos Config table**
  Stores credentials for Google Photos accounts

* **MongoDB Metadata Database Config table**
  Stores connection information for metadata databases

### 2. Metadata Databases

One or more MongoDB databases that store all photo and video metadata.

* **Media Item table**
  Stores metadata about each media item (photo or video)

* **Albums table**
  Stores information about albums and its album structure

## Security and Access

* The **Config Database is never exposed** to the Web UI or end users.
* Metadata databases are accessed only through the Web API.
* Authentication uses **Google OAuth2** between the Web UI and Web API.
* The Web API uses an allow list (environment variable) to restrict access.
* Future plans include support for multiple users and ACLs per user.

## Disclaimer

This project is intended **for educational purposes only** and **not for commercial use**. The maintainers disclaim all liability for damages or data loss resulting from the use of this software.

## License

Photos Drive is licensed under the **GNU General Public License (GPL)**.
Please refer to the `LICENSE.txt` file in the root of this repository for full license details.

---

Thank you for checking out Photos Drive!
Contributions, bug reports, and feature requests are welcome via GitHub issues and pull requests.
