import { wrap } from 'async-middleware'
import axios from 'axios'
import { json, Request, Response, Router } from 'express'
import { importPKCS8, SignJWT } from 'jose'
import { getConfig } from '../config'
import logger from '../utils/logger'

export const GOOGLE_LOGIN_PAGE_URL =
  'https://accounts.google.com/o/oauth2/v2/auth'

export const GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'

export const GOOGLE_USER_INFO_URL =
  'https://www.googleapis.com/oauth2/v2/userinfo'

export default async function () {
  const config = getConfig()

  const secretKey = await importPKCS8(config.accessTokenJwtPrivateKey, 'EdDSA')
  const expiryMillis = Number(process.env.JWT_EXPIRY_IN_MILLISECONDS) || 3600000

  const router: Router = Router()
  router.get('/auth/v1/google', (req: Request, res: Response) => {
    const baseUrl = `${GOOGLE_LOGIN_PAGE_URL}?client_id=${config.googleLoginClientId}&redirect_uri=${config.googleLoginCallbackUri}&response_type=code&scope=profile`

    if (req.query['select_account'] === 'true') {
      res.redirect(`${baseUrl}&prompt=select_account`)
    } else {
      res.redirect(baseUrl)
    }
  })

  router.post(
    '/auth/v1/google/token',
    json(),
    wrap(async (req: Request, res: Response) => {
      const code = req.body.code

      try {
        const tokenResponse = await axios.post(GOOGLE_TOKEN_URL, {
          code,
          client_id: config.googleLoginClientId,
          client_secret: config.googleLoginClientSecret,
          redirect_uri: config.googleLoginCallbackUri,
          grant_type: 'authorization_code'
        })

        const accessToken = tokenResponse.data.access_token
        const userInfo = await axios.get(GOOGLE_USER_INFO_URL, {
          headers: { Authorization: `Bearer ${accessToken}` }
        })

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
        logger.error(`Error authenticating ${error}`)
        res.status(500).json({ error: 'Authentication failed' })
      }
    })
  )

  return router
}
