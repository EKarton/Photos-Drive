import { Router } from 'express';
import exchangeGoogleToken from './exchange_google_token';
import getGoogleLoginUrl from './get_google_login_url';

export default async function () {
  const router: Router = Router();

  router.use(await getGoogleLoginUrl());
  router.use(await exchangeGoogleToken());

  return router;
}
