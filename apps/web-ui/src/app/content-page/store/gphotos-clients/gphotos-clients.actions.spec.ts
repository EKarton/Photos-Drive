import { Result, toSuccess } from '../../../shared/results/results';
import {
  GPhotosClientsListApiResponse,
  RefreshTokenApiResponse,
} from '../../services/webapi.service';
import {
  loadGPhotoClients,
  loadGPhotoClientsResults,
  loadRefreshTokenResult,
  refreshToken,
} from './gphotos-clients.actions';

describe('GPhoto Clients Actions', () => {
  it('should create an action to load GPhoto clients', () => {
    const action = loadGPhotoClients();
    expect(action.type).toBe('[GPhotoClients] Load GPhoto clients');
  });

  it('should create an action to load GPhoto clients results', () => {
    const mockResult: Result<GPhotosClientsListApiResponse> = toSuccess({
      gphotoClients: [],
    });

    const action = loadGPhotoClientsResults({ result: mockResult });

    expect(action.type).toBe('[GPhotoClients] Load GPhoto clients api success');
    expect(action.result).toEqual(mockResult);
  });

  it('should create an action to refresh token', () => {
    const clientId = 'client123';

    const action = refreshToken({ clientId });

    expect(action.type).toBe('[GPhotoClients] Refresh token');
    expect(action.clientId).toBe(clientId);
  });

  it('should create an action to load refresh token result', () => {
    const clientId = 'client123';
    const mockResult: Result<RefreshTokenApiResponse> = toSuccess({
      newToken: 'newToken',
    });

    const action = loadRefreshTokenResult({ clientId, result: mockResult });

    expect(action.type).toBe('[GPhotoClients] Loads new refresh token');
    expect(action.clientId).toBe(clientId);
    expect(action.result).toEqual(mockResult);
  });
});
