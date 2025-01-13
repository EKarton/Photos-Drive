import express from 'express'
import { mock } from 'jest-mock-extended'
import { importPKCS8, SignJWT } from 'jose'
import request from 'supertest'
import mediaItemsRouter from '../../src/routes/media_items'
import {
  MediaItem,
  MediaItemId
} from '../../src/services/metadata_store/MediaItems'
import {
  MediaItemNotFoundError,
  MediaItemsRepository
} from '../../src/services/metadata_store/MediaItemsRepository'
import { MongoDbClientNotFoundError } from '../../src/services/metadata_store/MongoDbClientsRepository'

describe('Media Items Router', () => {
  const originalEnv = process.env
  const fakePublicKey =
    '-----BEGIN PUBLIC KEY-----MCowBQYDK2VwAyEADPItlNZv8oKHe/TVm4b04lfw1tvY8dde52zmWzk8hg4=-----END PUBLIC KEY-----%'
  const fakePrivateKey =
    '-----BEGIN PRIVATE KEY-----MC4CAQAwBQYDK2VwBCIEIG2LxwXdQJFmm2E3jNdvVoDzFp1EUisEuzteaAd3Wpw7-----END PRIVATE KEY-----%'
  let token = ''

  beforeEach(async () => {
    jest.resetModules()
    process.env = {
      ...originalEnv,
      ACCESS_TOKEN_JWT_PUBLIC_KEY: fakePublicKey,
      ACCESS_TOKEN_JWT_PRIVATE_KEY: fakePrivateKey
    }

    const secretKey = await importPKCS8(
      process.env.ACCESS_TOKEN_JWT_PRIVATE_KEY || '',
      'EdDSA'
    )
    const tokenExpiryTime = new Date(Date.now() + 360000)
    token = await new SignJWT({ id: '1' })
      .setProtectedHeader({ alg: 'EdDSA' })
      .setIssuedAt()
      .setIssuer('Photos-Map-Web-Api')
      .setAudience('http://localhost:3000')
      .setExpirationTime(tokenExpiryTime)
      .sign(secretKey)
  })

  afterEach(() => {
    process.env = originalEnv
  })

  describe('GET /api/v1/media-items/:id', () => {
    it('should return 200 response with correct body given valid media item id', async () => {
      const mockMediaItem: MediaItem = {
        id: {
          clientId: 'mediaItemClientId1',
          objectId: 'mediaItem1'
        },
        file_name: 'dog.png',
        location: {
          latitude: 123,
          longitude: 456
        },
        gphotos_client_id: 'gPhotosClient1',
        gphotos_media_item_id: 'gPhotosMediaItem1'
      }
      const repo = mock<MediaItemsRepository>()
      repo.getMediaItemById.mockResolvedValue(mockMediaItem)
      const app = express()
      app.use(await mediaItemsRouter(repo))

      const res = await request(app)
        .get('/api/v1/media-items/mediaItemClientId1:mediaItem1')
        .set('Authorization', `Bearer ${token}`)

      expect(res.statusCode).toEqual(200)
      expect(res.body).toEqual({
        id: 'mediaItemClientId1:mediaItem1',
        fileName: 'dog.png',
        location: {
          latitude: 123,
          longitude: 456
        },
        gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem1'
      })
    })

    it('should return 200 response with correct body given valid media item id and no location', async () => {
      const mockMediaItem: MediaItem = {
        id: {
          clientId: 'mediaItemClientId1',
          objectId: 'mediaItem1'
        },
        file_name: 'dog.png',
        gphotos_client_id: 'gPhotosClient1',
        gphotos_media_item_id: 'gPhotosMediaItem1'
      }
      const repo = mock<MediaItemsRepository>()
      repo.getMediaItemById.mockResolvedValue(mockMediaItem)
      const app = express()
      app.use(await mediaItemsRouter(repo))

      const res = await request(app)
        .get('/api/v1/media-items/mediaItemClientId1:mediaItem1')
        .set('Authorization', `Bearer ${token}`)

      expect(res.statusCode).toEqual(200)
      expect(res.body).toEqual({
        id: 'mediaItemClientId1:mediaItem1',
        fileName: 'dog.png',
        location: null,
        gPhotosMediaItemId: 'gPhotosClient1:gPhotosMediaItem1'
      })
    })

    it('should return 404 response given MediaItemsRepository returns MongoDbClientNotFoundError', async () => {
      const repo = mock<MediaItemsRepository>()
      repo.getMediaItemById.mockRejectedValue(
        new MongoDbClientNotFoundError('mediaItemClientId1:mediaItem1')
      )
      const app = express()
      app.use(await mediaItemsRouter(repo))

      const res = await request(app)
        .get('/api/v1/media-items/mediaItemClientId1:mediaItem1')
        .set('Authorization', `Bearer ${token}`)

      expect(res.statusCode).toEqual(404)
      expect(res.body).toEqual({ error: 'Media item not found' })
    })

    it('should return 404 response given MediaItemsRepository returns MediaItemNotFoundError', async () => {
      const mediaItemId: MediaItemId = {
        clientId: 'mediaItemClientId1',
        objectId: 'mediaItem1'
      }
      const repo = mock<MediaItemsRepository>()
      repo.getMediaItemById.mockRejectedValue(
        new MediaItemNotFoundError(mediaItemId)
      )
      const app = express()
      app.use(await mediaItemsRouter(repo))

      const res = await request(app)
        .get('/api/v1/media-items/mediaItemClientId1:mediaItem1')
        .set('Authorization', `Bearer ${token}`)

      expect(res.statusCode).toEqual(404)
      expect(res.body).toEqual({ error: 'Media item not found' })
    })

    it('should return 500 response given MediaItemsRepository returns random error', async () => {
      const repo = mock<MediaItemsRepository>()
      repo.getMediaItemById.mockRejectedValue(new Error('Random error'))
      const app = express()
      app.use(await mediaItemsRouter(repo))

      const res = await request(app)
        .get('/api/v1/media-items/mediaItemClientId1:mediaItem1')
        .set('Authorization', `Bearer ${token}`)

      expect(res.statusCode).toEqual(500)
      expect(res.body).toEqual({})
    })
  })
})
