# Heatmap Design Doc

## Problem

## Solutions

### Option 1 (Preferred): Use H3 spatial indexing

### Option 2: Fetch N images one tile at a time

This approach is about breaking the globe / map into tiles at the current map's zoom level, and fetching an image at that tile.

More specifically, we break the map into tiles via this pseudocode:

```
```

Then, for each tile, we fetch an image from that tile. We can do so via this pseudocode:

```
```

Each time we add an image, we save the image's tile for every zoom level the map supports. We can do so via this pseudocode:

```py
MAX_ZOOM_LEVEL = 24

for zoom_level in range(0, MAX_ZOOM_LEVEL + 1):
    tile = compute_tile(image.latitude, image.longitude, zoom_level)
    insert_to_db({
        x: tile.x, 
        y: tile.y, 
        z: tile.z, 
        album_id: image.album.id, 
        image_id: image.id
    })
```

Pros:

- Fast:
  - The browser can compute a list of tiles easily for a given map
  - Fetching an image from a single tile is fast and cachable

Cons:

- At a particular zoom level, the browser can generate very large tiles, thereby creating a lot of blank spots when that tile only shows one image.
- More storage needed: when we add an image to the system, we need to save 24 variants of that image's tile for the 24 different zoom levels.

### Option 3: Load everything into UI

This approach is about loading all the images for an album or across all albums in the UI.

We already have an endpoint called /listMediaItems that will return a list of media items via pagination.
We are already using this when displaying a list of images in list form.

Pros:

- Simple

Cons:

- Too slow; fetching 1M+ photos onto the browser is too slow.

## Proposed Solution

The proposed solution is (1) due to the reasons above.

## Implementation
