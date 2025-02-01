import express from 'express';
import request from 'supertest';
import { verifyAuthentication } from '../../src/middlewares/authentication';
import { fakeAuthEnv, generateTestToken } from '../routes/utils/auth';
import { setupTestEnv } from '../routes/utils/env';

describe('verifyAuthentication()', () => {
  let cleanupTestEnvFn = () => {};

  beforeEach(() => {
    cleanupTestEnvFn = setupTestEnv({ ...fakeAuthEnv });
  });

  afterEach(() => {
    cleanupTestEnvFn();
  });

  it('should return 200, given correct access token', async () => {
    const token = await generateTestToken();

    const app = express();
    app.get(
      '/api/v1/protected-resource',
      await verifyAuthentication(),
      (_req, res) => {
        res.send('OK');
      }
    );

    const res = await request(app)
      .get('/api/v1/protected-resource')
      .set('Authorization', `Bearer ${token}`);

    expect(res.statusCode).toEqual(200);
    expect(res.text).toEqual('OK');
  });

  it('should return 401 with error message, given no access token', async () => {
    const app = express();
    app.get(
      '/api/v1/protected-resource',
      await verifyAuthentication(),
      (_req, res) => {
        res.send('OK');
      }
    );

    const res = await request(app).get('/api/v1/protected-resource');

    expect(res.statusCode).toEqual(401);
    expect(res.body.error).toEqual('Missing access token');
  });

  it('should return 401 with error message, given invalid access token', async () => {
    const app = express();
    app.get(
      '/api/v1/protected-resource',
      await verifyAuthentication(),
      (_req, res) => {
        res.send('OK');
      }
    );

    const res = await request(app)
      .get('/api/v1/protected-resource')
      .set('Authorization', `Bearer 1234`);

    expect(res.statusCode).toEqual(401);
    expect(res.body.error).toEqual('Invalid access token');
  });
});
