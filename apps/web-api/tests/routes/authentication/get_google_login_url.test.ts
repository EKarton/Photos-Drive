import cookieParser from 'cookie-parser';
import express from 'express';
import request from 'supertest';
import authRouter from '../../../src/routes/authentication';
import { fakeAuthEnv } from '../utils/auth';
import { setupTestEnv } from '../utils/env';

describe('GET auth/v1/google', () => {
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

  it('should return correct redirect uri with state and PKCE parameters', async () => {
    const app = express();
    app.use(cookieParser());
    app.use(await authRouter());

    const res = await request(app).get('/auth/v1/google');

    expect(res.statusCode).toEqual(200);
    const url = new URL(res.body.url);

    expect(url.origin).toEqual('https://accounts.google.com');
    expect(url.pathname).toEqual('/o/oauth2/v2/auth');
    expect(url.searchParams.get('client_id')).toEqual(fakeGoogleClientId);
    expect(url.searchParams.get('redirect_uri')).toEqual(fakeGoogleCallbackUri);
    expect(url.searchParams.get('response_type')).toEqual('code');
    expect(url.searchParams.get('scope')).toEqual('profile');
    expect(url.searchParams.get('state')).toBeDefined();
    expect(url.searchParams.get('code_challenge')).toBeDefined();
    expect(url.searchParams.get('code_challenge_method')).toEqual('S256');

    // Check cookies
    const cookies = res.get('Set-Cookie');
    expect(cookies).toBeDefined();
    expect(cookies).toEqual(
      expect.arrayContaining([
        expect.stringMatching(/^oauth_state=/),
        expect.stringMatching(/^oauth_code_verifier=/)
      ])
    );
  });

  it('should include prompt=select_account when query param is true', async () => {
    const app = express();
    app.use(cookieParser());
    app.use(await authRouter());

    const res = await request(app).get('/auth/v1/google?select_account=true');

    expect(res.statusCode).toEqual(200);
    const url = new URL(res.body.url);
    expect(url.searchParams.get('prompt')).toEqual('select_account');
  });
});
