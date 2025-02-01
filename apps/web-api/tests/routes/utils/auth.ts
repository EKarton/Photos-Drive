import { importPKCS8, SignJWT } from 'jose';

export const fakePublicKey =
  '-----BEGIN PUBLIC KEY-----MCowBQYDK2VwAyEADPItlNZv8oKHe/TVm4b04lfw1tvY8dde52zmWzk8hg4=-----END PUBLIC KEY-----%';

export const fakePrivateKey =
  '-----BEGIN PRIVATE KEY-----MC4CAQAwBQYDK2VwBCIEIG2LxwXdQJFmm2E3jNdvVoDzFp1EUisEuzteaAd3Wpw7-----END PRIVATE KEY-----%';

/** The fake required environment variables needed to generate an auth. */
export const fakeAuthEnv = {
  ACCESS_TOKEN_JWT_PUBLIC_KEY: fakePublicKey,
  ACCESS_TOKEN_JWT_PRIVATE_KEY: fakePrivateKey
};

/**
 * Generates a fake test token.
 *
 * @param privateKey a private key, with {@code fakePrivateKey} set as its default
 * @returns a fake test token, in a promise.
 */
export async function generateTestToken(
  privateKey: string = fakePrivateKey
): Promise<string> {
  const secretKey = await importPKCS8(privateKey, 'EdDSA');

  const tokenExpiryTime = new Date(Date.now() + 360000);
  return await new SignJWT({ id: '1' })
    .setProtectedHeader({ alg: 'EdDSA' })
    .setIssuedAt()
    .setIssuer('Photos-Map-Web-Api')
    .setAudience('http://localhost:3000')
    .setExpirationTime(tokenExpiryTime)
    .sign(secretKey);
}
