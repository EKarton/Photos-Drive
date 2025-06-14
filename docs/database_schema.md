# Database Scham

This doc presents the schema of each database.

## 1. Config Database

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

## 2. Metadata Databases

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
