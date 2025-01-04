import cookieParser from 'cookie-parser'
import express, { NextFunction, Request, Response } from 'express'
import request from 'supertest'
import { verifyAuthorization } from '../../src/middlewares/authorization'

describe('verifyAuthorization()', () => {
  const originalEnv = process.env

  beforeEach(() => {
    jest.resetModules()
    process.env = {
      ...originalEnv,
      ALLOWED_SUBJECT: '1234'
    }
  })

  afterEach(() => {
    process.env = originalEnv
  })

  it('should return 200, given correct subject', async () => {
    const mockAuthentication = (
      req: Request,
      _res: Response,
      next: NextFunction
    ) => {
      req.decodedAccessToken = { id: '1234' }
      next()
    }

    const app = express()
    app.use(cookieParser())
    app.get(
      '/api/v1/protected-resource',
      mockAuthentication,
      await verifyAuthorization(),
      (_req, res) => {
        res.send('OK')
      }
    )

    const res = await request(app).get('/api/v1/protected-resource')

    expect(res.statusCode).toEqual(200)
    expect(res.text).toEqual('OK')
  })

  it('should return 403, given incorrect subject', async () => {
    const mockAuthentication = (
      req: Request,
      _res: Response,
      next: NextFunction
    ) => {
      req.decodedAccessToken = { id: 'ABC' }
      next()
    }

    const app = express()
    app.use(cookieParser())
    app.get(
      '/api/v1/protected-resource',
      mockAuthentication,
      await verifyAuthorization(),
      (_req, res) => {
        res.send('OK')
      }
    )

    const res = await request(app).get('/api/v1/protected-resource')

    expect(res.statusCode).toEqual(403)
    expect(res.body).toEqual({ error: 'Not authorized to view this request' })
  })
})
