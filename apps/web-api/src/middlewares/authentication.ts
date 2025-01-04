import { NextFunction, Request, Response } from 'express'
import { importSPKI, jwtVerify } from 'jose'
import { getConfig } from '../config'
import logger from '../utils/logger'

export type DecodedAccessToken = {
  id: string
}

/**
 * Middleware that checks if the access token is valid
 * @returns an Express middleware
 */
export async function verifyAuthentication() {
  const publicKey = await importSPKI(
    getConfig().accessTokenJwtPublicKey,
    'EdDSA'
  )

  return async (req: Request, res: Response, next: NextFunction) => {
    const accessToken = req.cookies['access_token']
    if (!accessToken) {
      return res.status(401).json({ error: 'Missing access token' })
    }

    try {
      const decodedToken = await jwtVerify(accessToken, publicKey)
      req.decodedAccessToken = { id: decodedToken.payload.sub ?? '' }
      next()
    } catch (e) {
      logger.debug(`Error verifying token: ${e}`)

      return res.status(401).json({ error: 'Invalid access token' })
    }
  }
}
