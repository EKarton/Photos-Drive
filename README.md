# Photos Drive

[![Netlify Status](https://api.netlify.com/api/v1/badges/36282e46-c4ab-407f-8a6e-b6dbb4f40748/deploy-status)](https://app.netlify.com/projects/photosdrive-demo/deploys)

Photos Drive is a unified photo management platform designed to connect and display all your photos across different photo storage solutions in one place.

It syncs and uploads photos from your computer to configured databases and photo storage accounts using a CLI tool. A web UI then presents your photos in a list or map view, organized by nested albums that reflect the folder structure on your computer.

## Architecture Overview

The system consists of three main applications:

1. **CLI Client**
   A Python library and CLI tool that enables users to back up photos from their computer to the system.

2. **Web API**
   Reads photo metadata from MongoDB and serves it to the Web UI via REST endpoints.

3. **Web UI**
   A frontend application that fetches albums and photos from the Web API to display them to users in the browser.

## Technology Stack

* **Photo metadata storage:** MongoDB
* **Photo blob storage:** Google Photos
* **Authentication:** Google OAuth2 (between Web UI and Web API)
* **Access control:** Allow list configured via environment variables (future plans include multi-user ACLs)

## Databases

There are two types of databases in the system:

### 1. Config Database

Stores credentials and configuration details for metadata databases and photo storage accounts.

* **Root Album table**
  Contains exactly one row, which points to the root album location:

  ```json
  {
    "client_id": "<ObjectId>",  // The ID of the metadata database that contains the root album
    "object_id": "<ObjectId>"   // The ID of an album object in the metadata database's Albums table
  }
  ```

* **Google Photos Config table**
  Stores credentials for Google Photos accounts:

  ```json
  {
    "_id": "<ObjectId>",          // Unique ID for this config object
    "name": "<string>",           // Human-readable name for this Google Photos account config
    "read_write_credentials": {
      "token": "<string>",        // OAuth2 access token for Google Photos API
      "tokenUri": "<string>",     // URI to request a new access token
      "refreshToken": "<string>", // OAuth2 refresh token to renew the access token
      "clientId": "<string>",     // OAuth2 client ID for this application
      "clientSecret": "<string>"  // OAuth2 client secret for this application
    }
  }
  ```

* **MongoDB Metadata Database Config table**
  Stores connection information for metadata databases:

  ```json
  {
    "_id": "<ObjectId>",                    // Unique ID for this config object
    "name": "<string>",                     // Name of the metadata database (for identification)
    "read_only_connection_string": "<string>"  // MongoDB connection string for read-only access
  }
  ```

### 2. Metadata Databases

One or more MongoDB databases that store all photo and video metadata.

* **Media Item table**
  Stores metadata about each media item (photo or video):

  ```json
  {
    "_id": "<ObjectId>",               // Unique identifier for this media item
    "file_name": "<string>",           // Original filename of the photo or video
    "hash": "<bytes>",                 // Hash of the file contents (used for deduplication/integrity)
    "gphotos_client_id": "<string>",  // Reference to the Google Photos account storing this media
    "gphotos_media_item_id": "<string>", // The media item ID within Google Photos
    "album_id": "<ObjectId>",          // The album this media item belongs to
    "width": "<int>",                  // Width in pixels of the media
    "height": "<int>",                 // Height in pixels of the media
    "date_taken": "<Date>"             // Date and time when the media was originally taken
  }
  ```

* **Albums table**
  Stores information about albums and its album structure:

  ```json
  {
    "_id": "<ObjectId>",           // Unique identifier for this album
    "name": "<string>",            // Album name (e.g., folder name)
    "parent_album_id": "<ObjectId|null>"  // Reference to the parent album, or null if this is a root album
  }
  ```

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
