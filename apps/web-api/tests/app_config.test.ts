import { getAppConfig } from '../src/app_config';
import { fakeAuthEnv } from './routes/utils/auth';
import { setupTestEnv } from './routes/utils/env';

describe('app_config', () => {
  let cleanupEnv = () => {};

  afterEach(() => {
    cleanupEnv();
  });

  it('should throw an error if both VAULT_FILE_PATH and VAULT_MONGODB are not set', () => {
    const envWithNoVault = {
      ...fakeAuthEnv,
      CORS_FRONTEND_ENDPOINT: 'http://localhost'
    } as any;
    delete envWithNoVault.VAULT_FILE_PATH;
    delete envWithNoVault.VAULT_MONGODB;

    cleanupEnv = setupTestEnv(envWithNoVault);

    expect(() => getAppConfig()).toThrow(
      'Either VAULT_FILE_PATH or VAULT_MONGODB must be set'
    );
  });
});
