import { Album, albumIdToString } from '../../services/core/albums/Albums';

/** Serializes an album to a JSON object */
export function serializeAlbum(
  album: Album,
  numChildAlbums: number,
  numMediaItems: number
): object {
  return {
    id: `${album.id.clientId}:${album.id.objectId}`,
    albumName: album.name,
    parentAlbumId: album.parent_album_id
      ? albumIdToString(album.parent_album_id)
      : null,
    numChildAlbums,
    numMediaItems
  };
}
