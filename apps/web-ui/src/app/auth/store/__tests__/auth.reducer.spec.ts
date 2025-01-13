import { toFailure, toSuccess } from '../../../shared/results/results';
import { TokenResponse } from '../../services/webapi.service';
import * as authActions from '../auth.actions';
import { authReducer } from '../auth.reducer';
import { AuthState, buildInitialState } from '../auth.state';

describe('Auth Reducer', () => {
  let initialState: AuthState;

  beforeEach(() => {
    initialState = buildInitialState();
  });

  it('should update the state with loadAuthResult action', () => {
    const mockResult = toSuccess<TokenResponse>({
      accessToken: 'mockAccessToken',
      userProfileUrl: 'mockUserProfileUrl',
    });

    const action = authActions.loadAuthResult({ result: mockResult });
    const state = authReducer(initialState, action);

    expect(state.authToken).toBe('mockAccessToken');
    expect(state.userProfileUrl).toBe('mockUserProfileUrl');
  });

  it('should handle loadAuthResult action with missing data gracefully', () => {
    const mockResult = toFailure<TokenResponse>(new Error('Random error'));

    const action = authActions.loadAuthResult({ result: mockResult });
    const state = authReducer(initialState, action);

    expect(state.authToken).toBe('');
    expect(state.userProfileUrl).toBe('');
  });
});
