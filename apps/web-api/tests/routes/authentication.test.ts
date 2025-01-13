import express from 'express'
import nock from 'nock'
import request from 'supertest'
import authRouter from '../../src/routes/authentication'

const originalEnv = process.env

const fakePublicKey =
  '-----BEGIN PUBLIC KEY-----MCowBQYDK2VwAyEADPItlNZv8oKHe/TVm4b04lfw1tvY8dde52zmWzk8hg4=-----END PUBLIC KEY-----%'
const fakePrivateKey =
  '-----BEGIN PRIVATE KEY-----MC4CAQAwBQYDK2VwBCIEIG2LxwXdQJFmm2E3jNdvVoDzFp1EUisEuzteaAd3Wpw7-----END PRIVATE KEY-----%'
const fakeGoogleClientId = '123'
const fakeGoogleClientSecret = '456'
const fakeGoogleCallbackUri = 'http://localhost:3000/photos'

beforeEach(() => {
  jest.resetModules()
  process.env = {
    ...originalEnv,
    ACCESS_TOKEN_JWT_PUBLIC_KEY: fakePublicKey,
    ACCESS_TOKEN_JWT_PRIVATE_KEY: fakePrivateKey,
    GOOGLE_CLIENT_ID: fakeGoogleClientId,
    GOOGLE_CLIENT_SECRET: fakeGoogleClientSecret,
    GOOGLE_CALLBACK_URI: fakeGoogleCallbackUri
  }
})

afterEach(() => {
  process.env = originalEnv
})

describe('GET auth/v1/google', () => {
  it('should return correct redirect uri given no select_account query param', async () => {
    const app = express()
    app.use(await authRouter())

    const res = await request(app).get('/auth/v1/google')

    expect(res.statusCode).toEqual(302)
    expect(res.headers['location']).toEqual(
      'https://accounts.google.com/o/oauth2/v2/auth?client_id=123&redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Fphotos&response_type=code&scope=profile'
    )
  })

  it('should return correct redirect uri given no select_account query param', async () => {
    const app = express()
    app.use(await authRouter())

    const res = await request(app).get('/auth/v1/google?select_account=true')

    expect(res.statusCode).toEqual(302)
    expect(res.headers['location']).toEqual(
      'https://accounts.google.com/o/oauth2/v2/auth?client_id=123&redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Fphotos&response_type=code&scope=profile&prompt=select_account'
    )
  })
})

describe('POST auth/v1/google/token', () => {
  it('should return correct 200 response when code is correct', async () => {
    // Test setup: mock out the api to fetch the token
    nock('https://oauth2.googleapis.com').post('/token').reply(200, {
      access_token: 'access_token_123',
      expires_in: 3920,
      scope: 'profile',
      token_type: 'Bearer'
    })

    // Test setup: mock out the api to fetch the profile
    nock('https://www.googleapis.com').get('/oauth2/v2/userinfo').reply(200, {
      id: '110248495921238986420',
      name: 'Bob Smith',
      given_name: 'Bob',
      family_name: 'Smith',
      picture: 'https://lh4.googleusercontent.com/profile-pic.jpg'
    })

    const app = express()
    app.use(await authRouter())

    const res = await request(app)
      .post('/auth/v1/google/token')
      .send({ code: '1234' })

    expect(res.statusCode).toEqual(200)
    expect(res.body).toEqual({
      accessToken: expect.any(String),
      userProfileUrl: 'https://lh4.googleusercontent.com/profile-pic.jpg'
    })
  })

  it('should return correct 500 response when code is incorrect', async () => {
    // Test setup: mock out the api to fetch the token
    nock('https://www.googleapis.com').post('/oauth2/v4/token').reply(401)

    const app = express()
    app.use(await authRouter())

    const res = await request(app)
      .post('/auth/v1/google/token')
      .send({ code: '1234' })

    expect(res.statusCode).toEqual(500)
    expect(res.body).toEqual({ error: 'Authentication failed' })
  })
})
