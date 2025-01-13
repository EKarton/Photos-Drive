import express from 'express'
import { mock } from 'jest-mock-extended'
import { importPKCS8, SignJWT } from 'jose'
import request from 'supertest'
import gPhotosClientsRouter from '../../src/routes/gphoto_clients'
import {
  GPhotosClient,
  GPhotosCredentials
} from '../../src/services/blob_store/GPhotosClient'
import {
  GPhotosClientsRepository,
  NoGPhotosClientFoundError
} from '../../src/services/blob_store/GPhotosClientsRepository'

describe('GPhoto Clients Router', () => {
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

  describe('GET /api/v1/gphotos-clients', () => {
    it('should return 200 response', async () => {
      const client1Creds: GPhotosCredentials = {
        accessToken: 'client1AccessToken',
        refreshToken: 'client1RefreshToken',
        clientId: 'gClientId',
        clientSecret: 'gClientSecret'
      }
      const client2Creds: GPhotosCredentials = {
        accessToken: 'client2AccessToken',
        refreshToken: 'client2RefreshToken',
        clientId: 'gClientId',
        clientSecret: 'gClientSecret'
      }
      const client1 = new GPhotosClient('bob@gmail.com', client1Creds)
      const client2 = new GPhotosClient('sam@gmail.com', client2Creds)
      const repo = mock<GPhotosClientsRepository>()
      repo.getGPhotosClients.mockReturnValue([
        ['gPhotosClient1', client1],
        ['gPhotosClient2', client2]
      ])
      const app = express()
      app.use(await gPhotosClientsRouter(repo))

      const res = await request(app)
        .get('/api/v1/gphotos-clients')
        .set('Authorization', `Bearer ${token}`)

      expect(res.statusCode).toEqual(200)
      expect(res.body).toEqual({
        gphotoClients: [
          {
            id: 'gPhotosClient1',
            token: 'client1AccessToken'
          },
          {
            id: 'gPhotosClient2',
            token: 'client2AccessToken'
          }
        ]
      })
    })

    it('should return 500 response when GPhotosClientsRepository throws an error', async () => {
      const repo = mock<GPhotosClientsRepository>()
      repo.getGPhotosClients.mockImplementation(() => {
        throw new Error('Random error')
      })
      const app = express()
      app.use(await gPhotosClientsRouter(repo))

      const res = await request(app)
        .get('/api/v1/gphotos-clients')
        .set('Authorization', `Bearer ${token}`)

      expect(res.statusCode).toEqual(500)
      expect(res.body).toEqual({})
    })
  })

  describe('POST /api/v1/gphotos-clients/:id/token-refresh', () => {
    it('should return 200 response when token refresh is successful', async () => {
      const client1 = mock<GPhotosClient>()
      client1.refreshAccessToken.mockResolvedValue()
      client1.getCredentials.mockReturnValue({
        accessToken: 'client1AccessToken',
        refreshToken: 'client1RefreshToken',
        clientId: 'gClientId',
        clientSecret: 'gClientSecret'
      })
      const repo = mock<GPhotosClientsRepository>()
      repo.getGPhotosClientById.mockReturnValue(client1)
      const app = express()
      app.use(await gPhotosClientsRouter(repo))

      const res = await request(app)
        .post('/api/v1/gphotos-clients/gPhotosClient1/token-refresh')
        .set('Authorization', `Bearer ${token}`)

      expect(res.statusCode).toEqual(200)
      expect(res.body).toEqual({
        newToken: 'client1AccessToken'
      })
    })

    it('should return 404 when no client id is found', async () => {
      const repo = mock<GPhotosClientsRepository>()
      repo.getGPhotosClientById.mockImplementation(() => {
        throw new NoGPhotosClientFoundError('gPhotosClient1')
      })
      const app = express()
      app.use(await gPhotosClientsRouter(repo))

      const res = await request(app)
        .post('/api/v1/gphotos-clients/gPhotosClient1/token-refresh')
        .set('Authorization', `Bearer ${token}`)

      expect(res.statusCode).toEqual(404)
      expect(res.body).toEqual({ error: 'No GPhotos client found' })
    })

    it('should return 500 when random error is thrown', async () => {
      const repo = mock<GPhotosClientsRepository>()
      repo.getGPhotosClientById.mockImplementation(() => {
        throw new Error('Random error')
      })
      const app = express()
      app.use(await gPhotosClientsRouter(repo))

      const res = await request(app)
        .post('/api/v1/gphotos-clients/gPhotosClient1/token-refresh')
        .set('Authorization', `Bearer ${token}`)

      expect(res.statusCode).toEqual(500)
      expect(res.body).toEqual({})
    })
  })
})
