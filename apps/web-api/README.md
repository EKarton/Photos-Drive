# Photos-Drive-Web-Api

## Description

This is the web api app used to serve content to the web ui.

## Getting Started

1. First, create a Google OAuth2 project. Set up OAuth2 and get its client ID and client secrets.

2. Second, create a Mapbox account and grab it's API token.

3. Generate public and private keys by running:

   ```bash
   openssl genpkey -algorithm ed25519 -out private.pem
   openssl pkey -in private.pem -pubout -out public.pem
   ```

   It will create two files: `private.pem` and `public.pem`.

4. Now, run this to set the `private.pem` file as a single string:

   ```bash
   export ACCESS_TOKEN_JWT_PRIVATE_KEY=$(tr -d '\n' < private.pem)
   echo ${ACCESS_TOKEN_JWT_PUBLIC_KEY}
   ```

5. Similarly, run this to get the `public.pem` file as a single string:

   ```bash
   export ACCESS_TOKEN_JWT_PUBLIC_KEY=$(tr -d '\n' < public.pem)
   echo ${ACCESS_TOKEN_JWT_PUBLIC_KEY}
   ```

6. Next, create a `.env` file with these contents:

   ```env
   # Google OAuth2 client ID and client secrets
   GOOGLE_CLIENT_ID="YOUR_GOOGLE_OAUTH2_CLIENT_ID"
   GOOGLE_CLIENT_SECRET="YOUR_GOOGLE_OAUTH2_CLIENT_SECRET"
   GOOGLE_CALLBACK_URI="YOUR_GOOGLE_OAUTH2_CALLBACK_URI"

   # JWT
   ACCESS_TOKEN_JWT_PUBLIC_KEY="YOUR_JWT_PUBLIC_KEY_FROM_STEP_4"
   ACCESS_TOKEN_JWT_PRIVATE_KEY="YOUR_JWT_PRIVATE_KEY_FROM_STEP_5"
   ACCESS_TOKEN_ALLOWED_SUBJECT="YOUR_GOOGLE_ACCOUNT_ID"

   # Vault mongo db connection:
   VAULT_MONGODB="YOUR_READ_WRITE_CONNECTION_STRING_TO_THE_VAULT_IN_MONGODB"

   # If your vault is in the file:
   # VAULT_FILE_PATH="./../cli-client/test-config.conf"

   # Mapbox API token
   MAPBOX_API_TOKEN="YOUR_MAPBOX_API_TOKEN"

   PORT="3000"
   PINO_LOG_LEVEL="error"
   CORS_FRONTEND_ENDPOINT="http://localhost:4200"
   NUM_FORKS=1
   ```

7. Install dependencies and run the app by running: `pnpm install && pnpm dev`

8. It should launch the api on <http://localhost:3000>.

9. When you try to log in, in the logs, you will get this error:

   ```bash
   User XYZ is forbidden
   ```

   This is your unique Google account ID. Set `ACCESS_TOKEN_ALLOWED_SUBJECT` in your `.env` file to `XYZ`.

   If you want to expose your api to anyone, put `*` in `ACCESS_TOKEN_ALLOWED_SUBJECT`.

## Running them locally without Docker

1. Install dependencies by running: `pnpm install`

2. To run the code in dev mode: `pnpm dev`

3. To build production code: `pnpm build`

4. To run the production code: `pnpm start`

## Running them locally with Docker

1. To build the app, run `docker build -t photos-drive-web-api .`

2. To run the app, run `docker run -p 8080:3000 photos-drive-web-api`

## Running lints and tests

1. To find linting issues, run `pnpm lint`

2. To fix linting issues, run `pnpm lint:fix`

3. To run tests, run `pnpm test`. It automatically runs code coverage, and puts the code coverage under the `./coverage` folder.

4. To run tests for a particular file, run tests like this: `pnpm test:coverage tests/middlewares`
