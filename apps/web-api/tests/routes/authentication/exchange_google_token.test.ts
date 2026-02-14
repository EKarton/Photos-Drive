import cookieParser from 'cookie-parser';
import express from 'express';
import nock from 'nock';
import request from 'supertest';
import authRouter from '../../../src/routes/authentication';
import { fakeAuthEnv } from '../utils/auth';
import { setupTestEnv } from '../utils/env';

describe('POST auth/v1/google/token', () => {
  const fakeGoogleClientId = '123';
  const fakeGoogleClientSecret = '456';
  const fakeGoogleCallbackUri = 'http://localhost:3000/photos';
  const fakeMapboxApiToken = 'fakeMapboxApiToken1';

  let cleanupTestEnvFn = () => {};

  beforeEach(() => {
    jest.resetModules();
    cleanupTestEnvFn = setupTestEnv({
      ...fakeAuthEnv,
      GOOGLE_CLIENT_ID: fakeGoogleClientId,
      GOOGLE_CLIENT_SECRET: fakeGoogleClientSecret,
      GOOGLE_CALLBACK_URI: fakeGoogleCallbackUri,
      MAPBOX_API_TOKEN: fakeMapboxApiToken
    });
  });

  afterEach(() => {
    cleanupTestEnvFn();
  });

  it('should return correct 200 response when code and state are correct', async () => {
    const fakeState = 'state123';
    const fakeCodeVerifier = 'verifier123';

    // Test setup: mock out the api to fetch the token
    nock('https://oauth2.googleapis.com')
      .post('/token', (body) => {
        return body.code_verifier === fakeCodeVerifier;
      })
      .reply(200, {
        access_token: 'access_token_123',
        expires_in: 3920,
        scope: 'profile',
        token_type: 'Bearer'
      });

    // Test setup: mock out the api to fetch the profile
    nock('https://www.googleapis.com').get('/oauth2/v2/userinfo').reply(200, {
      id: '110248495921238986420',
      name: 'Bob Smith',
      given_name: 'Bob',
      family_name: 'Smith',
      picture: 'https://lh4.googleusercontent.com/profile-pic.jpg'
    });

    const app = express();
    app.use(cookieParser());
    app.use(await authRouter());

    const res = await request(app)
      .post('/auth/v1/google/token')
      .set('Cookie', [
        `oauth_state=${fakeState}`,
        `oauth_code_verifier=${fakeCodeVerifier}`
      ])
      .send({ code: '1234', state: fakeState });

    expect(res.statusCode).toEqual(200);
    expect(res.body).toEqual({
      accessToken: expect.any(String),
      userProfileUrl: 'https://lh4.googleusercontent.com/profile-pic.jpg',
      mapboxApiToken: fakeMapboxApiToken
    });

    // Verify cookies are cleared
    const cookies = res.get('Set-Cookie');
    expect(cookies).toBeDefined();
    if (cookies) {
      expect(
        cookies.some((c: string) => c.startsWith('oauth_state=;'))
      ).toBeTruthy();
      expect(
        cookies.some((c: string) => c.startsWith('oauth_code_verifier=;'))
      ).toBeTruthy();
    }
  });

  it('should return 403 when state is incorrect', async () => {
    const app = express();
    app.use(cookieParser());
    app.use(await authRouter());

    const res = await request(app)
      .post('/auth/v1/google/token')
      .set('Cookie', ['oauth_state=correct_state'])
      .send({ code: '1234', state: 'wrong_state' });

    expect(res.statusCode).toEqual(403);
    expect(res.body).toEqual({ error: 'Invalid state' });
  });

  it('should return correct 500 response when token exchange fails', async () => {
    const fakeState = 'state123';
    nock('https://oauth2.googleapis.com').post('/token').reply(401);

    const app = express();
    app.use(cookieParser());
    app.use(await authRouter());

    const res = await request(app)
      .post('/auth/v1/google/token')
      .set('Cookie', [`oauth_state=${fakeState}`])
      .send({ code: '1234', state: fakeState });

    expect(res.statusCode).toEqual(500);
    expect(res.body).toEqual({ error: 'Authentication failed' });
  });
});
