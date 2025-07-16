import express from 'express';
import { mock } from 'jest-mock-extended';
import request from 'supertest';
import heatmapRouter from '../../src/routes/heatmap';
import {
  HeatmapGenerator,
  HeatmapPoint
} from '../../src/services/maps_store/HeatmapGenerator';
import { AlbumId } from '../../src/services/metadata_store/Albums';
import { fakeAuthEnv, generateTestToken } from './utils/auth';
import { setupTestEnv } from './utils/env';

const MOCK_ROOT_ALBUM_ID: AlbumId = {
  clientId: 'albumClient1',
  objectId: 'albumObject0'
};

describe('Heatmap Router', () => {
  let cleanupTestEnvFn = () => {};
  let token = '';

  beforeEach(async () => {
    jest.resetModules();
    cleanupTestEnvFn = setupTestEnv({ ...fakeAuthEnv });
    token = await generateTestToken();
  });

  afterEach(() => {
    cleanupTestEnvFn();
  });

  it('returns 200 and correct heatmap points', async () => {
    const mockHeatmapGenerator = mock<HeatmapGenerator>();
    mockHeatmapGenerator.getHeatmapForTile.mockResolvedValue({
      points: [
        {
          cellId: 'abc123',
          count: 5,
          latitude: 37.7749,
          longitude: -122.4194,
          sampledMediaItemId: { clientId: 'mediaClient1', objectId: 'media1' }
        } as HeatmapPoint
      ]
    });

    const app = express();
    app.use(await heatmapRouter(MOCK_ROOT_ALBUM_ID, mockHeatmapGenerator));

    const res = await request(app)
      .get('/api/v1/maps/heatmap?x=1&y=2&z=3&albumId=albumClient1:albumObject1')
      .set('Authorization', `Bearer ${token}`);

    expect(res.statusCode).toBe(200);
    expect(res.body).toEqual({
      points: [
        {
          count: 5,
          latitude: 37.7749,
          longitude: -122.4194,
          sampledMediaItemId: 'mediaClient1:media1'
        }
      ]
    });
  });

  it('returns 200 when albumId is "root"', async () => {
    const mockHeatmapGenerator = mock<HeatmapGenerator>();
    mockHeatmapGenerator.getHeatmapForTile.mockResolvedValue({ points: [] });

    const app = express();
    app.use(await heatmapRouter(MOCK_ROOT_ALBUM_ID, mockHeatmapGenerator));

    const res = await request(app)
      .get('/api/v1/maps/heatmap?x=1&y=2&z=3&albumId=root')
      .set('Authorization', `Bearer ${token}`);

    expect(res.statusCode).toBe(200);
    expect(res.body).toEqual({ points: [] });
  });

  it('returns 400 if tile parameters are missing or invalid', async () => {
    const mockHeatmapGenerator = mock<HeatmapGenerator>();
    const app = express();
    app.use(await heatmapRouter(MOCK_ROOT_ALBUM_ID, mockHeatmapGenerator));

    const res = await request(app)
      .get('/api/v1/maps/heatmap?x=notANumber&y=2&z=3')
      .set('Authorization', `Bearer ${token}`);

    expect(res.statusCode).toBe(400);
    expect(res.body).toEqual({
      error: 'Bad request for tile id x=NaN, y=2, z=3'
    });
  });

  it('returns 200 with empty points array if no heatmap data', async () => {
    const mockHeatmapGenerator = mock<HeatmapGenerator>();
    mockHeatmapGenerator.getHeatmapForTile.mockResolvedValue({ points: [] });

    const app = express();
    app.use(await heatmapRouter(MOCK_ROOT_ALBUM_ID, mockHeatmapGenerator));

    const res = await request(app)
      .get('/api/v1/maps/heatmap?x=1&y=2&z=3')
      .set('Authorization', `Bearer ${token}`);

    expect(res.statusCode).toBe(200);
    expect(res.body).toEqual({ points: [] });
  });

  it('returns 500 on unexpected error', async () => {
    const mockHeatmapGenerator = mock<HeatmapGenerator>();
    mockHeatmapGenerator.getHeatmapForTile.mockRejectedValue(
      new Error('Unexpected failure')
    );

    const app = express();
    app.use(await heatmapRouter(MOCK_ROOT_ALBUM_ID, mockHeatmapGenerator));

    const res = await request(app)
      .get('/api/v1/maps/heatmap?x=1&y=2&z=3')
      .set('Authorization', `Bearer ${token}`);

    expect(res.statusCode).toBe(500);
  });
});
