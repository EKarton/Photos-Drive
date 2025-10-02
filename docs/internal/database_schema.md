# Schemas

## Global Object Identification

Every media item and album in the system can be uniquely identified using a **(clientId, objectId)** pair:

- **clientId** – The ID of the metadata database where the object resides.
- **objectId** – The ID of the document within that database’s collection.

This ensures global uniqueness across multiple databases. For example:

- A media item is identified by `clientId/objectId` where `objectId` is the `_id` of the document in the `Media Item` table of the given database.
- An album is identified by `clientId/objectId` where `objectId` is the `_id` of the document in the `Albums` table of the given database.

## Schema

This doc presents the schema of each store.

### 1. Config Store

Stores all credentials and configuration details for each database in the Metadata store, Heatmap store, and Vector store; and all photo storage accounts storing the blob storage for every photo and video in the system.

Every database used in the Metadata store, Heatmap store, and Vector store; and all photo storage accounts storing the blob storage for every photo and video in the system, needs to be registered in the Config store.

There is only one database in the Config store, and it has the following tables:

- **Root Album table**
  Contains exactly one document, which points to the root album location:

  ```json
  {
    "client_id": "ObjectId",  // The ID of the metadata database that contains the root album
    "object_id": "ObjectId"   // The ID of an album object in the metadata database's Albums table
  }
  ```

- **Google Photos Config table**
  Stores credentials for Google Photos accounts:

  ```json
  {
    "_id": "ObjectId",          // Unique ID for this config object
    "name": "string",           // Human-readable name for this Google Photos account config
    "read_write_credentials": {
      "token": "string",        // OAuth2 access token for Google Photos API
      "tokenUri": "string",     // URI to request a new access token
      "refreshToken": "string", // OAuth2 refresh token to renew the access token
      "clientId": "string",     // OAuth2 client ID for this application
      "clientSecret": "string"  // OAuth2 client secret for this application
    }
  }
  ```

- **Metadata Database Config table**
  Stores connection information for metadata databases:

  ```json
  {
    "_id": "ObjectId",                        // Unique ID for this config object
    "name": "string",                         // Name of the metadata database (for identification)
    "read_only_connection_string": "string",  // The read-only connection string to that database
    "read_write_connection_string": "string", // The read-write connection string to that database
  }
  ```

- **Vector Store Config table**
  Stores the connection info for all of the databases used in the vector store. This table has this schema:

  ```json
  {
    "_id": "ObjectId",                        // Unique ID for this database
    "name": "string",                         // Name of this database
    "type": "string",                         // The type of database (ex: MongoDB)
    "read_only_connection_string": "string",  // The read-only connection string to that database
    "read_write_connection_string": "string", // The read-write connection string to that database
  }
  ```

### 2. Metadata Store

The metadata store contains a collection of databases unioned together, where it stores all photo and video, and album metadata. The metadata store contains one or more databases, and each database in the Metadata Store contains these tables:

- **Media Item table**
  Stores metadata about each media item (photo or video):

  ```json
  {
    "_id": "ObjectId",                    // Unique identifier for this document
    "file_name": "string",                // Original filename of the photo or video
    "hash": "bytes",                      // Hash of the file contents (used for deduplication/integrity)
    "gphotos_client_id": "string",        // Reference to the Google Photos account storing this media
    "gphotos_media_item_id": "string",    // The media item ID containing the photo / video within Google Photos
    "album_id": "string",                 // The album this media item belongs to, in the format 'client_id/object_id'
    "width": "int",                       // Width in pixels of the media
    "height": "int",                      // Height in pixels of the media
    "date_taken": "Date"                  // Date and time when the media was originally taken
  }
  ```

- **Albums table**
  Stores information about albums and its album structure. Each MongoDB database has these tables:

  ```json
  {
    "_id": "ObjectId",                  // Unique identifier for this album
    "name": "string",                   // Album name (e.g., folder name)
    "parent_album_id": "string | null"  // Album ID to the parent album, or null if this is a root album.
                                          // The album ID is in the format 'client_id/object_id'
  }
  ```

### 3. Heatmap Store

The heatmap store contains a collection of databases unioned together, where it is stores spatial index data for all media items. As described in the [heatmap project](./heatmap_doc.md), For each media item, its geographic location (latitude/longitude) is projected onto a slippy map tile grid at every zoom level from 0 to MAX_ZOOM_LEVEL (24).

At each zoom level, the media item is mapped to exactly one tile (x, y, z), and a record is stored in the database, linking the tile to the media item and its album.

Each MongoDB database has these tables:

- **Map Cells table**

  Stores all of the images' H3 cells for each zoom level:

  ```json
  {
    "_id": "ObjectId",        // Some auto-generated ID we don't use
    "media_item_id": "string",  // The ID of the media item
                                // The media item ID is in the format 'client_id/object_id'
    "cell_id": "string",        // The cell ID, in x/y/z format
    "album_id": "string",       // The album ID that this media item belongs to
  }
  ```
