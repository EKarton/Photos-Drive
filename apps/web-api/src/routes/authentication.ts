import { wrap } from 'async-middleware'
import axios from 'axios'
import { json, Request, Response, Router } from 'express'
import { importPKCS8, SignJWT } from 'jose'
import passport from 'passport'
import { Profile, Strategy, VerifyCallback } from 'passport-google-oauth20'
import { getConfig } from '../config'
import logger from '../utils/logger'

export default async function () {
  const config = getConfig()

  const secretKey = await importPKCS8(config.accessTokenJwtPrivateKey, 'EdDSA')
  const expiryMillis = Number(process.env.JWT_EXPIRY_IN_MILLISECONDS) || 3600000

  const router: Router = Router()
  router.get('/auth/v1/google', (_req: Request, res: Response) => {
    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${config.googleLoginClientId}&redirect_uri=${config.googleLoginCallbackUri}&response_type=code&scope=profile&prompt=select_account`
    res.redirect(authUrl)
  })

  router.post(
    '/auth/v1/google/token',
    json(),
    wrap(async (req: Request, res: Response) => {
      const code = req.body.code

      try {
        const tokenResponse = await axios.post(
          'https://oauth2.googleapis.com/token',
          {
            code,
            client_id: config.googleLoginClientId,
            client_secret: config.googleLoginClientSecret,
            redirect_uri: config.googleLoginCallbackUri,
            grant_type: 'authorization_code'
          }
        )

        const accessToken = tokenResponse.data.access_token
        const userInfo = await axios.get(
          'https://www.googleapis.com/oauth2/v2/userinfo',
          {
            headers: { Authorization: `Bearer ${accessToken}` }
          }
        )

        const profile = userInfo.data
        const profilePhoto = profile.picture

        const tokenExpiryTime = new Date(Date.now() + expiryMillis)
        const token = await new SignJWT()
          .setProtectedHeader({ alg: 'EdDSA' })
          .setIssuedAt()
          .setIssuer('Sharded-Photos-Drive-WebApi')
          .setAudience('Sharded-Photos-Drive-WebUI')
          .setSubject(profile.id)
          .setExpirationTime(tokenExpiryTime)
          .sign(secretKey)

        res.json({
          accessToken: token,
          userProfileUrl: profilePhoto
        })
      } catch (error) {
        logger.debug(`Error authenticating ${error}`)
        res.status(500).json({ error: 'Authentication failed' })
      }
    })
  )

  return router
}
