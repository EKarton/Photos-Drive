# Setup

This guide illustrates the steps needed to get your Photos Drive web api up and running locally.

## Table of Contents

- [Step 1: Setting up your .env file](#step-1-setting-up-your-env-file)
- [Step 2: Running the web api locally](#step-2-running-the-web-api-locally)

## Step 1: Setting up your .env file

1. First, create a new [Google Cloud Project](https://console.cloud.google.com) for the Web API.

2. Set up OAuth2 in your new GCP project to get its client ID and client secrets.

   > Note: **do not** use the OAuth2 credentials you made from your CLI client to authenticate with your Web API, since that will make attackers access your photos illegally

3. Then, create a new [Mapbox](https://www.mapbox.com) account and grab it's API token.

4. Generate public and private keys by running:

   ```bash
   openssl genpkey -algorithm ed25519 -out private.pem
   openssl pkey -in private.pem -pubout -out public.pem
   ```

   It will create two files: `private.pem` and `public.pem`.

5. Now, run this to set the `private.pem` file as a single string:

   ```bash
   export ACCESS_TOKEN_JWT_PRIVATE_KEY=$(tr -d '\n' < private.pem)
   echo ${ACCESS_TOKEN_JWT_PUBLIC_KEY}
   ```

6. Similarly, run this to get the `public.pem` file as a single string:

   ```bash
   export ACCESS_TOKEN_JWT_PUBLIC_KEY=$(tr -d '\n' < public.pem)
   echo ${ACCESS_TOKEN_JWT_PUBLIC_KEY}
   ```

7. Next, create a `.env` file with these contents:

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

## Step 2: Running the web api locally

Once you get your `.env` file ready, you can start running the web api locally.

1. Install dependencies and run the app by running: `pnpm install && pnpm dev`

2. It should launch the api on <http://localhost:3000>.

3. When you try to log in, in the logs, you will get this error:

   ```bash
   User XYZ is forbidden
   ```

   This is your unique Google account ID. Set `ACCESS_TOKEN_ALLOWED_SUBJECT` in your `.env` file to `XYZ`.

   If you want to expose your api to anyone, put `*` in `ACCESS_TOKEN_ALLOWED_SUBJECT`.
