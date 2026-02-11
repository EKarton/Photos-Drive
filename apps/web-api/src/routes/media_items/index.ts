import { Router } from 'express';
import { GPhotosClientsRepository } from '../../services/blob_store/gphotos/GPhotosClientsRepository';
import { MediaItemsStore } from '../../services/metadata_store/MediaItemsStore';
import { BaseVectorStore } from '../../services/vector_stores/BaseVectorStore';
import bulkGetMediaItemDetails from './bulk_get_media_item_details';
import getMediaItemDetails from './get_media_item_details';
import getMediaItemImage from './get_media_item_image';
import sampleMediaItems from './sample_media_items';
import searchMediaItems from './search_media_items';
import vectorSearchMediaItems from './vector_search_media_items';

export default async function (
  mediaItemsRepo: MediaItemsStore,
  gPhotoClientRepo: GPhotosClientsRepository,
  vectorStore: BaseVectorStore
) {
  const router: Router = Router();

  router.use(await bulkGetMediaItemDetails(mediaItemsRepo));
  router.use(await getMediaItemDetails(mediaItemsRepo));
  router.use(await getMediaItemImage(mediaItemsRepo, gPhotoClientRepo));
  router.use(await sampleMediaItems(mediaItemsRepo));
  router.use(await searchMediaItems(mediaItemsRepo));
  router.use(await vectorSearchMediaItems(mediaItemsRepo, vectorStore));

  return router;
}
