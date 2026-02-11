import { Router } from 'express';
import rateLimit from 'express-rate-limit';

export default function () {
  const router: Router = Router();
  router.get(
    '/api/v1/health',
    rateLimit({
      windowMs: 15 * 60 * 1000, // 15 minutes
      max: 100
    }),
    (_, res) => {
      res.sendStatus(200);
    }
  );

  return router;
}
