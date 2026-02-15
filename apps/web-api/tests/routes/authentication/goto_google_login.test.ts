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

  it('should return correct redirect uri given no select_account query param', async () => {
    const app = express();
    app.use(await authRouter());

    const res = await request(app).get('/auth/v1/google');

    expect(res.statusCode).toEqual(302);
    expect(res.headers['location']).toEqual(
      'https://accounts.google.com/o/oauth2/v2/auth?client_id=123&redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Fphotos&response_type=code&scope=profile'
    );
  });

  it('should return correct redirect uri given no select_account query param', async () => {
    const app = express();
    app.use(await authRouter());

    const res = await request(app).get('/auth/v1/google?select_account=true');

    expect(res.statusCode).toEqual(302);
    expect(res.headers['location']).toEqual(
      'https://accounts.google.com/o/oauth2/v2/auth?client_id=123&redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Fphotos&response_type=code&scope=profile&prompt=select_account'
    );
  });
});
