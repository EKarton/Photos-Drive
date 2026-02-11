import { Request, Response, Router } from 'express';
import { getAppConfig } from '../../app_config';

export const GOOGLE_LOGIN_PAGE_URL =
  'https://accounts.google.com/o/oauth2/v2/auth';

export default async function () {
  const config = getAppConfig();
  const router: Router = Router();

  router.get('/auth/v1/google', (req: Request, res: Response) => {
    const url = new URL(GOOGLE_LOGIN_PAGE_URL);
    const params = new URLSearchParams({
      client_id: config.googleLoginClientId,
      redirect_uri: config.googleLoginCallbackUri,
      response_type: 'code',
      scope: 'profile'
    });

    if (req.query['select_account'] === 'true') {
      params.append('prompt', 'select_account');
    }

    url.search = params.toString();
    res.redirect(url.toString());
  });

  return router;
}
