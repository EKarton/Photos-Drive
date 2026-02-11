import { Router } from 'express';
import { AlbumId } from '../../services/core/albums/Albums';
import { AlbumsStore } from '../../services/core/albums/BaseAlbumsStore';
import { MediaItemsStore } from '../../services/core/media_items/BaseMediaItemsStore';
import getAlbumDetails from './get_album_details';
import listAlbums from './list_albums';

export default async function (
  rootAlbumId: AlbumId,
  albumsRepo: AlbumsStore,
  mediaItemsRepo: MediaItemsStore
) {
  const router: Router = Router();

  router.use(await getAlbumDetails(rootAlbumId, albumsRepo, mediaItemsRepo));
  router.use(await listAlbums(rootAlbumId, albumsRepo, mediaItemsRepo));

  return router;
}
