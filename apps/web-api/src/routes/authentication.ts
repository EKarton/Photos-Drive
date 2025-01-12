import { wrap } from 'async-middleware'
import { Request, Response, Router } from 'express'
import { importPKCS8, SignJWT } from 'jose'
import passport from 'passport'
import { Profile, Strategy, VerifyCallback } from 'passport-google-oauth20'
import { getConfig } from '../config'

export default async function () {
  const config = getConfig()

  passport.use(
    new Strategy(
      {
        clientID: config.googleLoginClientId,
        clientSecret: config.googleLoginClientSecret,
        callbackURL: config.googleLoginCallbackUri
      },
      function (
        _accessToken: string,
        _refreshToken: string,
        profile: Profile,
        done: VerifyCallback
      ) {
        return done(null, profile)
      }
    )
  )

  const secretKey = await importPKCS8(config.accessTokenJwtPrivateKey, 'EdDSA')

  const expiryMillis = Number(process.env.JWT_EXPIRY_IN_MILLISECONDS) || 3600000

  const router: Router = Router()
  router.get(
    '/auth/v1/google',
    passport.authenticate('google', {
      scope: ['profile'],
      prompt: 'select_account'
    })
  )

  router.get('/auth/v1/google/failed', (_req: Request, res: Response) => {
    res.status(401).send('Login failed')
  })

  router.get(
    '/auth/v1/google/callback',
    passport.authenticate('google', {
      failureRedirect: '/auth/v1/google/failed',
      session: false
    }),
    wrap(async (req: Request, res: Response) => {
      const profile = req.user as Profile

      const tokenExpiryTime = new Date(Date.now() + expiryMillis)
      const token = await new SignJWT()
        .setProtectedHeader({ alg: 'EdDSA' })
        .setIssuedAt()
        .setIssuer('Sharded-Photos-Drive-WebApi')
        .setAudience('Sharded-Photos-Drive-WebUI')
        .setSubject(profile.id)
        .setExpirationTime(tokenExpiryTime)
        .sign(secretKey)

      res.cookie('access_token', token, {
        secure: config.accessTokenDomain !== 'localhost',
        httpOnly: true,
        sameSite: 'lax', //config.accessTokenDomain === 'localhost' ? 'lax' : 'none',
        expires: tokenExpiryTime,
        domain: 'sharded-photos-drive-web-api.azurewebsites.net',
        path: '/'
      })

      const profilePhoto = profile.photos?.find((photo) => photo.value)?.value
      res.cookie('user_profile_url', profilePhoto, {
        secure: config.accessTokenDomain !== 'localhost',
        httpOnly: false,
        sameSite: 'lax', //config.accessTokenDomain === 'localhost' ? 'lax' : 'none',
        expires: tokenExpiryTime,
        domain: 'sharded-photos-drive-web-api.azurewebsites.net',
        path: '/'
      })

      res.setHeader('Access-Control-Allow-Origin', config.frontendEndpoint)
      res.setHeader('Access-Control-Allow-Credentials', 'true')

      res.redirect(config.loginCallbackUrl)
    })
  )

  router.get(
    '/auth/v1/google/logout',
    wrap(async (_req: Request, res: Response) => {
      res.clearCookie('access_token')
      res.clearCookie('user_profile_url')
      res.redirect('/')
    })
  )

  return router
}
