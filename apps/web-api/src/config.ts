/**
 * A set of config variables
 */
export type Config = {
  /** The client id of the Google OAuth2 login flow. */
  googleLoginClientId: string

  /** The client secret of the Google OAuth2 login flow. */
  googleLoginClientSecret: string

  /**
   * The callback uri of the Google OAuth2 login flow.
   * It should match what is in GCP.
   */
  googleLoginCallbackUri: string

  /** The JWT public key used to generate the access token. */
  accessTokenJwtPublicKey: string

  /** The JWT private key used to generate the access token. */
  accessTokenJwtPrivateKey: string

  /** The allowed domains for the access token. */
  accessTokenDomain: string

  /** The allowed subject for the access token. */
  accessTokenAllowedSubject: string

  /** The url for when authentication happens. */
  loginCallbackUrl: string

  /** The server port. */
  serverPort: number

  /** The file path to the vault. */
  vaultFilePath: string

  /** The MongoDB connection string to the vault */
  vaultMongoDb: string

  /** The frontend endpoint */
  frontendEndpoint: string
}

/**
 * Returns a set of config variables from environment variables.
 * @returns a set of config variables
 */
export function getConfig(): Config {
  return {
    googleLoginClientId: process.env.GOOGLE_CLIENT_ID || '',
    googleLoginClientSecret: process.env.GOOGLE_CLIENT_SECRET || '',
    googleLoginCallbackUri: process.env.GOOGLE_CALLBACK_URI || '',
    accessTokenJwtPublicKey: process.env.JWT_PUBLIC_KEY || '',
    accessTokenJwtPrivateKey: process.env.JWT_PRIVATE_KEY || '',
    accessTokenAllowedSubject: process.env.ALLOWED_SUBJECT || '',
    accessTokenDomain: process.env.ACCESS_TOKEN_DOMAIN || '',
    loginCallbackUrl: process.env.LOGIN_CALLBACK_URL || '',
    serverPort: parseInt(process.env.PORT || '3000'),
    vaultFilePath: process.env.VAULT_FILE_PATH || '',
    vaultMongoDb: process.env.VAULT_MONGODB || '',
    frontendEndpoint: process.env.FRONTEND_ENDPOINT || ''
  }
}
