/**
 * A set of config variables
 */
export type Config = {
  /** The client id of the Google OAuth2 login flow. */
  googleLoginClientId: string

  /** The client secret of the Google OAuth2 login flow. */
  googleLoginClientSecret: string

  /** The callback uri of the Google OAuth2 login flow (should match whats in GCP).  */
  googleLoginCallbackUri: string

  /** The JWT public key used to generate the access token. */
  accessTokenJwtPublicKey: string

  /** The JWT private key used to generate the access token. */
  accessTokenJwtPrivateKey: string

  /** The allowed subject for the access token. */
  accessTokenAllowedSubject: string

  /** The server port. */
  serverPort: number

  /** The file path to the vault. */
  vaultFilePath: string

  /** The MongoDB connection string to the vault */
  vaultMongoDb: string

  /** The frontend endpoint for CORS. */
  corsFrontendEndpoint: string
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
    accessTokenJwtPublicKey: process.env.ACCESS_TOKEN_JWT_PUBLIC_KEY || '',
    accessTokenJwtPrivateKey: process.env.ACCESS_TOKEN_JWT_PRIVATE_KEY || '',
    accessTokenAllowedSubject: process.env.ACCESS_TOKEN_ALLOWED_SUBJECT || '',
    serverPort: parseInt(process.env.PORT || '3000'),
    vaultFilePath: process.env.VAULT_FILE_PATH || '',
    vaultMongoDb: process.env.VAULT_MONGODB || '',
    corsFrontendEndpoint: process.env.CORS_FRONTEND_ENDPOINT || ''
  }
}
