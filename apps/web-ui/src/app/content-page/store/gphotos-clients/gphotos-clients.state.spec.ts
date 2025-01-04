import { Map as ImmutableMap } from 'immutable';

import { Result, toPending, toSuccess } from '../../../shared/results/results';
import {
  initialState,
  selectGPhotosClientsState,
  selectToken,
} from './gphotos-clients.state';
import { FEATURE_KEY, GPhotoClientsState } from './gphotos-clients.state';

describe('GPhotoClients State Selectors', () => {
  it('should select the entire GPhotoClients state', () => {
    const result = selectGPhotosClientsState.projector(initialState);

    expect(result).toEqual(initialState);
  });

  it('should return pending result when no clients are present', () => {
    const tokenId = 'nonExistingId';
    const result = selectToken(tokenId)({ [FEATURE_KEY]: initialState });

    expect(result).toEqual(toPending<string>());
  });

  it('should return a client token when it exists', () => {
    const tokenId = 'clientId';
    const clientToken = 'someClientToken';
    const clientResult: Result<ImmutableMap<string, Result<string>>> =
      toSuccess(
        ImmutableMap<string, Result<string>>().set(
          tokenId,
          toSuccess(clientToken),
        ),
      );
    const initialState: GPhotoClientsState = {
      idToClientResult: clientResult,
    };

    const result = selectToken(tokenId)({ [FEATURE_KEY]: initialState });

    expect(result).toEqual(toSuccess(clientToken));
  });

  it('should return pending for a client token that does not exist', () => {
    const tokenId = 'clientId';
    const clientToken = 'someClientToken';
    const clientResult: Result<ImmutableMap<string, Result<string>>> =
      toSuccess(
        ImmutableMap<string, Result<string>>().set(
          tokenId,
          toSuccess(clientToken),
        ),
      );
    const initialState: GPhotoClientsState = {
      idToClientResult: clientResult,
    };

    const result = selectToken('123')({ [FEATURE_KEY]: initialState });

    expect(result).toEqual(toPending<string>());
  });
});
