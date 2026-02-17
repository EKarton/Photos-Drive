import { Router } from 'express';
import { GPhotosClientsRepository } from '../../services/core/storage/gphotos/GPhotosClientsRepository';
import getGPhotosMediaItemDetails from './gphotos/get_gphotos_media_item_details';

export default async function (gPhotoClientRepo: GPhotosClientsRepository) {
  const router: Router = Router();

  router.use(await getGPhotosMediaItemDetails(gPhotoClientRepo));

  return router;
}
