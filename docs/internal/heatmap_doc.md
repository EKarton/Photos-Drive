# Heatmap One Pager Design

## Background

We want to show a heatmap of the images on a globe. It should be able to:

1. Update the heatmap and a thumbnail of the images as the user zoom and pans on the globe efficiently
2. Display a heatmap based on the region on the map

## Design

This approach is built on [Uber’s H3 geospatial index system](https://www.uber.com/blog/h3), where it breaks the globe / map into tiles at the current map's zoom level, and fetching an image at that tile.

More specifically, we first break the map into H3 tiles via this pseudocode:

```py
bounds = this.map.getBounds()
zoom = Math.max(1, Math.floor(this.map.getZoom()))

north = clampLat(bounds.getNorth())
south = clampLat(bounds.getSouth())
east = clampLng(bounds.getEast())
west = clampLng(bounds.getWest())

[xTop, yTop] = tilebelt.pointToTile(west, north, zoom)
[xBottom, yBottom] = tilebelt.pointToTile(east, south, zoom)

tiles = []

for x in range(xTop, xBottom + 1):
  for y in range(yTop, yBottom + 1):
    const tile = f'{x}/{y}/{zoom}'
    tiles.add(tile)

return tiles
```

where `map.getBounds()` returns the bounds of the map shown in the viewport in latitude and longitude coordinates, `tilebelt.pointToTile` maps the bounds of the viewport to the most left x, most right x, top y, and bottom y of the viewport, and then generate the  each tile is identified by `x/y/z` coordinates.

Then, for each tile, we compute the number of H3 cells that reside in that tile. We then fetch the images in those cells. We can do so via this pseudocode:

```py
bbox = tilebelt.tileToBBOX([tile.x, tile.y, tile.z])
polygon = [
  [bbox[0], bbox[1]], # SW: [minLon, minLat]
  [bbox[2], bbox[1]], # SE: [maxLon, minLat]
  [bbox[2], bbox[3]], # NE: [maxLon, maxLat]
  [bbox[0], bbox[3]], # NW: [minLon, maxLat]
  [bbox[0], bbox[1]]  # Close polygon
]
h3_res = tileZoomToH3Resolution(tile.z)
cell_ids = polygonToCells([polygon], h3Res, true)

for cell_id in cell_ids:
  find_image_in_cell(cell_id, h3_res)
```

where `tileZoomToH3Resolution` maps the map's zoom level to the H3 zoom level, and `polygonToCells` converts a tile into a list of cells inside that tile.

Each time we add an image to the Photos Drive, we save the image's tile for every zoom level the map supports. We can do so via this pseudocode:

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
