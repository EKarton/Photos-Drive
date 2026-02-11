# Photos-Drive-Web-Api

## Description

This is the web api app used to serve content to the web ui.

## Getting Started

Refer to [this guide](./docs/setup.md) for a step-by-step guide on how to set up the web api.

## Running locally without Docker

1. Install dependencies by running: `pnpm install`

1. To run the code in dev mode: `pnpm dev`

1. To build production code: `pnpm build`

1. To run the production code: `pnpm start`

## Running locally with Docker

1. To build the app, run `docker build -t photos-drive-web-api .`

1. To run the app, run `docker run -p 8080:3000 photos-drive-web-api`

## Running lints and tests

1. To find linting issues, run `pnpm lint`

1. To fix linting issues, run `pnpm lint:fix`

1. To run tests, run `pnpm test`. It automatically runs code coverage, and puts the code coverage under the `./coverage` folder.

1. To run tests for a particular file, run tests like this: `pnpm test:coverage tests/middlewares`
