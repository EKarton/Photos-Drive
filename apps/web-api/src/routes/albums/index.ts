import { Router } from 'express';
import { AlbumId } from '../../services/metadata_store/Albums';
import { AlbumsStore } from '../../services/metadata_store/AlbumsStore';
import { MediaItemsStore } from '../../services/metadata_store/MediaItemsStore';
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
