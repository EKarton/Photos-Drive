import { Router } from 'express'

export default function () {
  const router: Router = Router()
  router.get('/api/v1/health', (_, res) => {
    res.sendStatus(200)
  })

  return router
}
