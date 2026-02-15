import { createHash, randomBytes } from 'crypto';
import { Request, Response, Router } from 'express';
import rateLimit from 'express-rate-limit';
import { getAppConfig } from '../../app_config';
import { rateLimitKey } from '../../utils/rateLimitKey';

export const GOOGLE_LOGIN_PAGE_URL =
  'https://accounts.google.com/o/oauth2/v2/auth';

export default async function () {
  const config = getAppConfig();
  const router: Router = Router();

  router.get(
    '/auth/v1/google',
    rateLimit({
      windowMs: 15 * 60 * 1000,
      max: 5,
      standardHeaders: true,
      legacyHeaders: false,
      keyGenerator: rateLimitKey
    }),
    (req: Request, res: Response) => {
      const state = randomBytes(32).toString('hex');
      const codeVerifier = randomBytes(32).toString('hex');
      const codeChallenge = createHash('sha256')
        .update(codeVerifier)
        .digest('base64url');

      const cookieOptions = {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'none' as const,
        maxAge: 15 * 60 * 1000, // 15 minutes
        partitioned: true
      };

      res.cookie('oauth_state', state, cookieOptions);
      res.cookie('oauth_code_verifier', codeVerifier, cookieOptions);

      const url = new URL(GOOGLE_LOGIN_PAGE_URL);
      const params = new URLSearchParams({
        client_id: config.googleLoginClientId,
        redirect_uri: config.googleLoginCallbackUri,
        response_type: 'code',
        scope: 'profile',
        state: state,
        code_challenge: codeChallenge,
        code_challenge_method: 'S256'
      });

      if (req.query['select_account'] === 'true') {
        params.append('prompt', 'select_account');
      }

      url.search = params.toString();

      res.json({
        url: url.toString()
      });
    }
  );

  return router;
}
