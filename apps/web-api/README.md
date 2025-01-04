# Sharded-Photos-Drive-Web-Api

## Running them locally without Docker

1. Install dependencies by running: `pnpm install`

2. To run the code in dev mode: `pnpm dev`

3. To build production code: `pnpm build`

4. To run the production code: `pnpm start`

## Running them locally with Docker

1. To build the app, run `docker build -t sharded-photos-drive-web-api .`

2. To run the app, run `docker run -p 8080:3000 sharded-photos-drive-web-api`

## Running lints and tests

1. To find linting issues, run `pnpm lint`

2. To fix linting issues, run `pnpm lint:fix`

3. To run tests, run `pnpm test`

4. To run tests with coverage, run `pnpm test --coverage`

5. To run tests with coverage for a particular file, run tests like this: `pnpm test --coverage src/middlewares`

## Generating keys

1. Generate public and private keys by running:

```
openssl genpkey -algorithm ed25519 -out private.pem
openssl pkey -in private.pem -pubout -out public.pem
```

It will create two files: `private.pem` and `public.pem`.

2. Now, run this to set the `private.pem` file as the environment variable `JWT_PRIVATE_KEY`:

```
export JWT_PRIVATE_KEY=$(tr -d '\n' < private.pem)
```

3. Similarly, run this to set the `public.pem` file as the environment variable `JWT_PUBLIC_KEY`:

```
export JWT_PUBLIC_KEY=$(tr -d '\n' < public.pem)
```
