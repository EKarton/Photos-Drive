import { z } from 'zod';

/**
 * A set of config variables
 */
export type AppConfig = {
  /** The client id of the Google OAuth2 login flow. */
  googleLoginClientId: string;

  /** The client secret of the Google OAuth2 login flow. */
  googleLoginClientSecret: string;

  /** The callback uri of the Google OAuth2 login flow (should match whats in GCP).  */
  googleLoginCallbackUri: string;

  /** The JWT public key used to generate the access token. */
  accessTokenJwtPublicKey: string;

  /** The JWT private key used to generate the access token. */
  accessTokenJwtPrivateKey: string;

  /** The allowed subject for the access token. */
  accessTokenAllowedSubject: string;

  /** The server port. */
  serverPort: number;

  /** The number of trust proxies. */
  trustProxyHops: number;

  /** The file path to the vault. */
  vaultFilePath: string;

  /** The MongoDB connection string to the vault */
  vaultMongoDb: string;

  /** The frontend endpoint for CORS. */
  corsFrontendEndpoint: string;

  /** The Mapbox API token. */
  mapboxApiToken: string;
};

const appConfigSchema = z
  .object({
    GOOGLE_CLIENT_ID: z.string().min(1),
    GOOGLE_CLIENT_SECRET: z.string().min(1),
    GOOGLE_CALLBACK_URI: z.string().min(1),
    ACCESS_TOKEN_JWT_PUBLIC_KEY: z.string().min(1),
    ACCESS_TOKEN_JWT_PRIVATE_KEY: z.string().min(1),
    ACCESS_TOKEN_ALLOWED_SUBJECT: z.string().default('*'),
    PORT: z.coerce.number().default(3000),
    TRUST_PROXY_HOPS: z.coerce.number().default(1),
    VAULT_FILE_PATH: z.string().default(''),
    VAULT_MONGODB: z.string().default(''),
    CORS_FRONTEND_ENDPOINT: z.string().default('*'),
    MAPBOX_API_TOKEN: z.string().default('')
  })
  .refine((data) => data.VAULT_FILE_PATH || data.VAULT_MONGODB, {
    message: 'Either VAULT_FILE_PATH or VAULT_MONGODB must be set',
    path: ['VAULT_FILE_PATH', 'VAULT_MONGODB']
  });

/**
 * Returns a set of config variables from environment variables.
 * @returns a set of config variables
 */
export function getAppConfig(): AppConfig {
  const env = appConfigSchema.parse(process.env);

  return {
    googleLoginClientId: env.GOOGLE_CLIENT_ID,
    googleLoginClientSecret: env.GOOGLE_CLIENT_SECRET,
    googleLoginCallbackUri: env.GOOGLE_CALLBACK_URI,
    accessTokenJwtPublicKey: env.ACCESS_TOKEN_JWT_PUBLIC_KEY,
    accessTokenJwtPrivateKey: env.ACCESS_TOKEN_JWT_PRIVATE_KEY,
    accessTokenAllowedSubject: env.ACCESS_TOKEN_ALLOWED_SUBJECT,
    serverPort: env.PORT,
    trustProxyHops: env.TRUST_PROXY_HOPS,
    vaultFilePath: env.VAULT_FILE_PATH,
    vaultMongoDb: env.VAULT_MONGODB,
    corsFrontendEndpoint: env.CORS_FRONTEND_ENDPOINT,
    mapboxApiToken: env.MAPBOX_API_TOKEN
  };
}
