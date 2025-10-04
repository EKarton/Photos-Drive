# Setup

This guide illustrates the steps needed to get your Photos Drive web api up and running locally.

## Table of Contents

- [Step 1: Setting up your .env file](#step-1-setting-up-your-env-file)
- [Step 2: Running the web api locally](#step-2-running-the-web-api-locally)

## Step 1: Setting up your .env file

1. First, follow [this guide](./setup_oauth2.md) to create a new GCP project for the Web API, create a new OAuth2 client, and obtain the client ID and client secrets from your newly created OAuth2 client.

   > Note: **do not** use the same OAuth2 credentials you made from your CLI client to authenticate with your Web API, since that will make attackers access your photos illegally from your Web UI.

1. Then, create a new [Mapbox](https://www.mapbox.com) account and grab it's API token.

1. Generate public and private keys by running:

   ```bash
   openssl genpkey -algorithm ed25519 -out private.pem
   openssl pkey -in private.pem -pubout -out public.pem
   ```

   It will create two files: `private.pem` and `public.pem`.

1. Now, run this to set the `private.pem` file and `public.pem` file as a single string:

   ```bash
   export ACCESS_TOKEN_JWT_PRIVATE_KEY=$(tr -d '\n' < private.pem)
   export ACCESS_TOKEN_JWT_PUBLIC_KEY=$(tr -d '\n' < public.pem)

   echo ${ACCESS_TOKEN_JWT_PUBLIC_KEY}
   echo ${ACCESS_TOKEN_JWT_PUBLIC_KEY}
   ```

1. Next, create a `.env` file with these contents:

   ```env
   # Google OAuth2 client ID and client secrets
   GOOGLE_CLIENT_ID="YOUR_GOOGLE_OAUTH2_CLIENT_ID"
   GOOGLE_CLIENT_SECRET="YOUR_GOOGLE_OAUTH2_CLIENT_SECRET"
   GOOGLE_CALLBACK_URI="http://localhost:4200/auth/v1/google/callback"

   # JWT
   ACCESS_TOKEN_JWT_PUBLIC_KEY="YOUR_JWT_PUBLIC_KEY_FROM_STEP_4"
   ACCESS_TOKEN_JWT_PRIVATE_KEY="YOUR_JWT_PRIVATE_KEY_FROM_STEP_5"
   ACCESS_TOKEN_ALLOWED_SUBJECT="XXX"

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

   where:
   - `YOUR_GOOGLE_OAUTH2_CLIENT_ID` and `YOUR_GOOGLE_OAUTH2_CLIENT_SECRET` is the client ID and client secret from step 1.
   - `YOUR_JWT_PUBLIC_KEY` and `YOUR_JWT_PRIVATE_KEY` is the public and private key generated from step 4.
   - `YOUR_READ_WRITE_CONNECTION_STRING_TO_THE_VAULT_IN_MONGODB` is the MongoDB connection string to the config, if your config is in MongoDB.
   - `MAPBOX_API_TOKEN` is the Mapbox api token generated from step 2.

## Step 2: Running the web api locally

Once you get your `.env` file ready, you can start running the web api locally.

1. Install dependencies and run the app by running: `pnpm install && pnpm dev`

1. It should launch the api on <http://localhost:3000>.

1. When you try to log in, in the logs, you will get this error:

   ```bash
   User XYZ is forbidden
   ```

   This is your unique Google account ID. Set `ACCESS_TOKEN_ALLOWED_SUBJECT` in your `.env` file to `XYZ`.

   If you want to expose your api to anyone, put `*` in `ACCESS_TOKEN_ALLOWED_SUBJECT`.
