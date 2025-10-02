# Architecture Overview

The architecture of the entire app looks like this:

The system consists of three main applications:

1. **[CLI Client](./apps/cli-client/README.md)**
   A Python library and CLI tool that enables users to back up photos from their computer to the system.

2. **[Web API](./apps/web-api/README.md)**
   Reads photo metadata from MongoDB and serves it to the Web UI via REST endpoints.

3. **[Web UI](./apps/web-ui/README.md)**
   A frontend application that fetches albums and photos from the Web API to display them to users in the browser.

## Technology Stack

* **Photo metadata store:** MongoDB
* **Vector store:** MongoDB
* **Maps store:** MongoDB
* **Photo blob storage:** Google Photos
* **Authentication:** Google OAuth2 (between Web UI and Web API)
* **Access control:** Allow list configured via environment variables (future plans include multi-user ACLs)

## Data Stores

The entire system uses different data stores to store different types of data. Refer to [this guide](./docs/database_schema.md) for more info on their schemas. In essence, there are four types of data stores in the system:

### 1. Config Store

Stores credentials and configuration details for metadata databases, map databases, vector databases, and photo storage accounts.

* **Root Album table**
  Contains exactly one row, which points to the root album location.

* **Google Photos Config table**
  Stores credentials for Google Photos accounts

* **MongoDB Metadata Database Config table**
  Stores connection information for metadata databases

### 2. Metadata Store

One or more MongoDB databases that store all photo and video metadata.

* **Media Items table**
  Stores metadata about each media item (photo or video)

* **Albums table**
  Stores information about albums and its album structure

### 3. Maps Store

One or more MongoDB databases that store the H3 spatial index for all photos / videos with geolocation.

* **Heatmap table**
  Stores the H3 spatial index for all photos / videos with geolocation.

### 4. Vector Store

One or more MongoDB databases that stores the image embeddings for all photos.

## Security and Access

* The **Config Database is never exposed** to the Web UI or end users.
* Metadata databases are accessed only through the Web API.
* Authentication uses **Google OAuth2** between the Web UI and Web API.
* The Web API uses an allow list (environment variable) to restrict access.
* Future plans include support for multiple users and ACLs per user.
