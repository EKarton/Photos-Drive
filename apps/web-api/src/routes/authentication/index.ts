import { Router } from 'express';
import exchangeGoogleToken from './exchange_google_token';
import gotoGoogleLogin from './goto_google_login';

export default async function () {
  const router: Router = Router();

  router.use(await gotoGoogleLogin());
  router.use(await exchangeGoogleToken());

  return router;
}
