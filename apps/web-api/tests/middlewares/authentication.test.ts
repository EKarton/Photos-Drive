import cookieParser from 'cookie-parser'
import express from 'express'
import { importPKCS8, SignJWT } from 'jose'
import request from 'supertest'
import { verifyAuthentication } from '../../src/middlewares/authentication'

describe('verifyAuthentication()', () => {
  const originalEnv = process.env
  const fakePublicKey =
    '-----BEGIN PUBLIC KEY-----MCowBQYDK2VwAyEADPItlNZv8oKHe/TVm4b04lfw1tvY8dde52zmWzk8hg4=-----END PUBLIC KEY-----%'
  const fakePrivateKey =
    '-----BEGIN PRIVATE KEY-----MC4CAQAwBQYDK2VwBCIEIG2LxwXdQJFmm2E3jNdvVoDzFp1EUisEuzteaAd3Wpw7-----END PRIVATE KEY-----%'

  beforeEach(() => {
    jest.resetModules()
    process.env = {
      ...originalEnv,
      JWT_PUBLIC_KEY: fakePublicKey,
      JWT_PRIVATE_KEY: fakePrivateKey
    }
  })

  afterEach(() => {
    process.env = originalEnv
  })

  it('should return 200, given correct access token', async () => {
    const secretKey = await importPKCS8(fakePrivateKey, 'EdDSA')
    const tokenExpiryTime = new Date(Date.now() + 360000)
    const token = await new SignJWT({ id: '1' })
      .setProtectedHeader({ alg: 'EdDSA' })
      .setIssuedAt()
      .setIssuer('Photos-Map-Web-Api')
      .setAudience('http://localhost:3000')
      .setExpirationTime(tokenExpiryTime)
      .sign(secretKey)

    const app = express()
    app.use(cookieParser())
    app.get(
      '/api/v1/protected-resource',
      await verifyAuthentication(),
      (_req, res) => {
        res.send('OK')
      }
    )

    const res = await request(app)
      .get('/api/v1/protected-resource')
      .set('Cookie', [`access_token=${token}`])

    expect(res.statusCode).toEqual(200)
    expect(res.text).toEqual('OK')
  })

  it('should return 401 with error message, given no access token', async () => {
    const app = express()
    app.use(cookieParser())
    app.get(
      '/api/v1/protected-resource',
      await verifyAuthentication(),
      (_req, res) => {
        res.send('OK')
      }
    )

    const res = await request(app).get('/api/v1/protected-resource')

    expect(res.statusCode).toEqual(401)
    expect(res.body.error).toEqual('Missing access token')
  })

  it('should return 401 with error message, given invalid access token', async () => {
    const app = express()
    app.use(cookieParser())
    app.get(
      '/api/v1/protected-resource',
      await verifyAuthentication(),
      (_req, res) => {
        res.send('OK')
      }
    )

    const res = await request(app)
      .get('/api/v1/protected-resource')
      .set('Cookie', ['access_token=1234'])

    expect(res.statusCode).toEqual(401)
    expect(res.body.error).toEqual('Invalid access token')
  })
})
