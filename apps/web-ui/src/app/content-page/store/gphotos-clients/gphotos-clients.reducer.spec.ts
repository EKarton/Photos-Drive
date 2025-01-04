import { Map as ImmutableMap } from 'immutable';

import { hasSucceed, Result, toSuccess } from '../../../shared/results/results';
import * as gphotoClientsActions from './gphotos-clients.actions';
import { gphotosClientsReducer } from './gphotos-clients.reducer';
import { GPhotoClientsState, initialState } from './gphotos-clients.state';

describe('GPhotos Clients Reducer', () => {
  it('should return the initial state', () => {
    const action = { type: 'NOOP' };

    const state = gphotosClientsReducer(undefined, action);

    expect(state).toEqual(initialState);
  });

  it('should handle loadGPhotoClientsResults action', () => {
    const clientsData = {
      gphotoClients: [
        { id: 'client1', token: 'token1' },
        { id: 'client2', token: 'token2' },
      ],
    };

    const action = gphotoClientsActions.loadGPhotoClientsResults({
      result: toSuccess(clientsData),
    });
    const newState = gphotosClientsReducer(initialState, action);

    expect(hasSucceed(newState.idToClientResult)).toBeTrue();
    expect(newState.idToClientResult.data!.get('client1')).toEqual(
      toSuccess<string>('token1'),
    );
    expect(newState.idToClientResult.data!.get('client2')).toEqual(
      toSuccess<string>('token2'),
    );
  });

  it('should handle loadRefreshTokenResult action', () => {
    const clientId = 'client1';
    const initialClientState: GPhotoClientsState = {
      ...initialState,
      idToClientResult: toSuccess(
        ImmutableMap<string, Result<string>>().set(
          clientId,
          toSuccess('oldToken'),
        ),
      ),
    };

    const action = gphotoClientsActions.loadRefreshTokenResult({
      clientId,
      result: toSuccess({ newToken: 'newToken' }),
    });
    const state = gphotosClientsReducer(initialClientState, action);

    const expectedState: GPhotoClientsState = {
      ...initialClientState,
      idToClientResult: toSuccess(
        ImmutableMap<string, Result<string>>().set(
          'client1',
          toSuccess('newToken'),
        ),
      ),
    };
    expect(state).toEqual(expectedState);
  });
});
