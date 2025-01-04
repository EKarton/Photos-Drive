import { wrap } from 'async-middleware'
import { Router } from 'express'
import { verifyAuthentication } from '../middlewares/authentication'
import { verifyAuthorization } from '../middlewares/authorization'
import { MediaItemId } from '../services/metadata_store/MediaItems'
import {
  MediaItemNotFoundError,
  MediaItemsRepository
} from '../services/metadata_store/MediaItemsRepository'
import { MongoDbClientNotFoundError } from '../services/metadata_store/MongoDbClientsRepository'

export default async function (mediaItemsRepo: MediaItemsRepository) {
  const router: Router = Router()

  router.get(
    '/api/v1/media-items/:id',
    await verifyAuthentication(),
    await verifyAuthorization(),
    wrap(async (req, res) => {
      const rawMediaItemId = req.params.id
      const rawMediaItemIdParts = rawMediaItemId.split(':')
      const mediaItemId: MediaItemId = {
        clientId: rawMediaItemIdParts[0],
        objectId: rawMediaItemIdParts[1]
      }

      try {
        const mediaItem = await mediaItemsRepo.getMediaItemById(mediaItemId)
        const response = {
          id: `${mediaItem.id.clientId}:${mediaItem.id.objectId}`,
          fileName: mediaItem.file_name,
          location: mediaItem.location
            ? {
                latitude: mediaItem.location.latitude,
                longitude: mediaItem.location.longitude
              }
            : null,
          gPhotosMediaItemId: `${mediaItem.gphotos_client_id}:${mediaItem.gphotos_media_item_id}`
        }

        return res.status(200).json(response)
      } catch (error) {
        if (error instanceof MongoDbClientNotFoundError) {
          return res.status(404).json({
            error: 'Media item not found'
          })
        }
        if (error instanceof MediaItemNotFoundError) {
          return res.status(404).json({
            error: 'Media item not found'
          })
        }

        throw error
      }
    })
  )

  return router
}
