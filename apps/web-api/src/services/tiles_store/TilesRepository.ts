import { AlbumId } from '../metadata_store/Albums';
import { MediaItemId } from '../metadata_store/MediaItems';

/**
 * A class that represents the ID of a Tile.
 * A tile is defined by (x, y, z) coordinates.
 */
export interface TileId {
  x: number;
  y: number;
  z: number;
}

/** A class that stores the tiles from the database. */
export interface TilesRepository {
  /**
   * Returns the total number of media items that reside within a tile.
   * A tile is defined by (x, y, z).
   * If an album is specified, it will return media item IDs under that album.
   *
   * @param tileId The tile's ID
   * @param albumId The album ID to search under
   */

  getNumMediaItems(
    tileId: TileId,
    albumId: AlbumId | undefined
  ): Promise<number>;

  /**
   * Returns a list of media item IDs (up to the limit) that reside within a tile.
   * If an album is specified, it will return media item IDs under that album.
   *
   * @param tileId The tile's ID
   * @param albumId The album ID to search under
   * @param limit The max. number of media item IDs to return
   */
  getMediaItems(
    tileId: TileId,
    albumId: AlbumId | undefined,
    limit: number | undefined
  ): Promise<MediaItemId[]>;
}
