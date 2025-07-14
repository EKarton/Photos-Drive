import { AlbumId } from '../metadata_store/Albums';
import { MediaItemId } from '../metadata_store/MediaItems';

export type CellId = string;

/**
 * A class that represents a cell in the database.
 */
export interface MapCell {
  cellId: CellId;
  albumId: AlbumId;
  mediaItemId: MediaItemId;
}

/** A class that fetches thee map cells from the database. */
export interface MapCellsRepository {
  /**
   * Returns the total number of media items that reside in a cell.
   * If an album is specified, it will return the number of media item IDs under that album.
   *
   * @param cellId The cell ID
   * @param albumId The album ID
   */

  getNumMediaItemInCell(
    cellId: CellId,
    albumId: AlbumId | undefined
  ): Promise<number>;

  getNumMediaItemsInCells(
    cellIds: CellId[],
    albumId: AlbumId | undefined
  ): Promise<Map<CellId, number>>;

  /**
   * Returns a list of media item IDs (up to the limit) that reside within a list of cells.
   * If an album is specified, it will return media item IDs under that album.
   * If a limit is specified, it will return up to max. {@code limit} per cell.
   *
   * @param tileId The tile's ID
   * @param albumId The album ID to search under
   * @param limit The max. number of media item IDs to return
   */
  getMediaItems(
    cellIds: CellId[],
    albumId: AlbumId | undefined,
    limit: number | undefined
  ): Promise<MediaItemId[]>;
}
