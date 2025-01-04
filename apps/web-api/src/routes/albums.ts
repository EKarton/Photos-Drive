import { wrap } from 'async-middleware'
import { Request, Response, Router } from 'express'
import { verifyAuthentication } from '../middlewares/authentication'
import { verifyAuthorization } from '../middlewares/authorization'
import { AlbumId } from '../services/metadata_store/Albums'
import {
  AlbumNotFoundError,
  AlbumsRepository
} from '../services/metadata_store/AlbumsRepository'
import { MongoDbClientNotFoundError } from '../services/metadata_store/MongoDbClientsRepository'

export default async function (
  rootAlbumId: AlbumId,
  albumsRepo: AlbumsRepository
) {
  const router: Router = Router()

  router.get(
    '/api/v1/albums/root',
    await verifyAuthentication(),
    await verifyAuthorization(),
    wrap(async (_, res: Response) => {
      const rawAlbumId = `${rootAlbumId.clientId}:${rootAlbumId.objectId}`
      return res.redirect(`/api/v1/albums/${rawAlbumId}`)
    })
  )

  router.get(
    '/api/v1/albums/:albumId',
    await verifyAuthentication(),
    await verifyAuthorization(),
    wrap(async (req: Request, res: Response) => {
      const rawAlbumId = req.params.albumId
      const rawAlbumIdParts = rawAlbumId.split(':')
      const albumId: AlbumId = {
        clientId: rawAlbumIdParts[0],
        objectId: rawAlbumIdParts[1]
      }

      try {
        const album = await albumsRepo.getAlbumById(albumId)
        const response = {
          id: `${album.id.clientId}:${album.id.objectId}`,
          albumName: album.name,
          parentAlbumId: album.parent_album_id
            ? `${album.parent_album_id.clientId}:${album.parent_album_id.objectId}`
            : null,
          childAlbumIds: album.child_album_ids.map(
            (id) => `${id.clientId}:${id.objectId}`
          ),
          mediaItemIds: album.media_item_ids.map(
            (id) => `${id.clientId}:${id.objectId}`
          )
        }
        return res.status(200).json(response)
      } catch (error) {
        if (error instanceof MongoDbClientNotFoundError) {
          return res.status(404).json({ error: 'Album not found' })
        }
        if (error instanceof AlbumNotFoundError) {
          return res.status(404).json({ error: 'Album not found' })
        }

        throw error
      }
    })
  )

  return router
}
