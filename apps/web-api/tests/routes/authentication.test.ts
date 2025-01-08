import cookieParser from 'cookie-parser'
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
const fakeLoginCallbackUri = 'http://localhost:4200/content/root'
const fakeAccessTokenDomain = 'localhost'

beforeEach(() => {
  jest.resetModules()
  process.env = {
    ...originalEnv,
    JWT_PUBLIC_KEY: fakePublicKey,
    JWT_PRIVATE_KEY: fakePrivateKey,
    GOOGLE_CLIENT_ID: fakeGoogleClientId,
    GOOGLE_CLIENT_SECRET: fakeGoogleClientSecret,
    GOOGLE_CALLBACK_URI: fakeGoogleCallbackUri,
    LOGIN_CALLBACK_URL: fakeLoginCallbackUri,
    ACCESS_TOKEN_DOMAIN: fakeAccessTokenDomain
  }
})

afterEach(() => {
  process.env = originalEnv
})

describe('GET auth/v1/google', () => {
  it('should return correct redirect uri', async () => {
    const app = express()
    app.use(cookieParser())
    app.use(await authRouter())

    const res = await request(app).get('/auth/v1/google')

    expect(res.statusCode).toEqual(302)
    expect(res.headers['location']).toEqual(
      'https://accounts.google.com/o/oauth2/v2/auth?prompt=select_account&response_type=code&redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Fphotos&scope=profile&client_id=123'
    )
  })
})

describe('GET auth/v1/google/callback', () => {
  test.each([
    {
      accessTokenDomain: 'localhost'
    },
    {
      accessTokenDomain: 'photoarchives.netlify.app'
    }
  ])(
    'should set access token and redirect user to correct uri, given correct auth path and accessTokenDomain=$accessTokenDomain',
    async ({ accessTokenDomain }) => {
      // Test setup: mock out accessTokenDomain
      process.env.ACCESS_TOKEN_DOMAIN = accessTokenDomain

      // Test setup: mock out the api to fetch the token
      nock('https://www.googleapis.com').post('/oauth2/v4/token').reply(200, {
        access_token: 'access_token_123',
        expires_in: 3920,
        scope: 'profile',
        token_type: 'Bearer'
      })

      // Test setup: mock out the api to fetch the profile
      nock('https://www.googleapis.com')
        .get('/oauth2/v3/userinfo?access_token=access_token_123')
        .reply(200, {
          id: '110248495921238986420',
          name: 'Bob Smith',
          given_name: 'Bob',
          family_name: 'Smith',
          picture: 'https://lh4.googleusercontent.com/profile-pic.jpg'
        })

      const app = express()
      app.use(cookieParser())
      app.use(await authRouter())

      const res = await request(app).get('/auth/v1/google/callback?code=1234')

      expect(res.statusCode).toEqual(302)
      expect(res.headers['set-cookie'].length).toEqual(2)
      expect(
        res.headers['set-cookie'][0].startsWith('access_token')
      ).toBeTruthy()
      expect(
        res.headers['set-cookie'][1].startsWith('user_profile_url')
      ).toBeTruthy()
      expect(res.headers['location']).toEqual(fakeLoginCallbackUri)
    }
  )
})

describe('GET auth/v1/google/failed', () => {
  it('should return 401', async () => {
    const app = express()
    app.use(cookieParser())
    app.use(await authRouter())

    const res = await request(app).get('/auth/v1/google/failed')

    expect(res.statusCode).toEqual(401)
    expect(res.text).toEqual('Login failed')
  })
})

describe('GET auth/v1/google/logout', () => {
  it('should return 301, clear cookies, and return back to home page', async () => {
    const app = express()
    app.use(cookieParser())
    app.use(await authRouter())

    const res = await request(app)
      .get('/auth/v1/google/logout')
      .set('Cookie', ['access_token=123'])

    expect(res.statusCode).toEqual(302)
    expect(res.headers['set-cookie']).toEqual([
      'access_token=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT'
    ])
    expect(res.headers['location']).toEqual('/')
  })
})
