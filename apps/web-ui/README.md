# Sharded Photos Drive Web UI

## Description

This project is a web app for Sharded Photos Drive. This web app allows users to list and see their photos and videos on a web browser. This web app will only read photos and videos and never modify anything in the database.

This project was generated using [Angular CLI](https://github.com/angular/angular-cli) version 19.0.6.

## Getting Started

### Installation

1. First, install angular by running:

    ```bash
    npm install -g @angular/cli
    ```

2. Next, install the project's dependencies by running:

    ```bash
    npm install
    ```

3. Then, create a `.env` file to store your environment variables, like:

    ```text
    NG_APP_LOGIN_URL=http://localhost:3000/auth/v1/google
    NG_APP_WEB_API_ENDPOINT=http://localhost:3000
    ```

    where:
    - `NG_APP_LOGIN_URL`: is the login url of your [web-api](./../web-api)
    - `NG_APP_WEB_API_ENDPOINT`: is the domain of your [web-api](./../web-api)

4. Next, run:

    ```bash
    ng serve
    ```

    It should start a local development server of this app to <http://localhost:4200>. Once the server is running, open your browser and navigate to <http://localhost:4200>. The application will automatically reload whenever you modify any of the source files.

## Development

### Code scaffolding

Angular CLI includes powerful code scaffolding tools. To generate a new component, run:

```bash
ng generate component component-name
```

For a complete list of available schematics (such as `components`, `directives`, or `pipes`), run:

```bash
ng generate --help
```

### Building

To build the project run:

```bash
ng build
```

This will compile your project and store the build artifacts in the `dist/` directory. By default, the production build optimizes your application for performance and speed.

### Linting

To check for code styles, run

```bash
npm run lint
```

To automatically fix errors in code styles, run:

```bash
npm run lint:fix
```

### Running unit tests

To run all unit tests, run:

```bash
ng test --watch=false --no-progress --browsers=ChromeHeadless --code-coverage
```

It will check for code coverage, which you can see from the `./coverage` directory.

To only run specific unit test(s), run:

```bash
ng test --watch=false --no-progress --browsers=ChromeHeadless --code-coverage --include=<path-to-test-file>
```

For instance, to only run tests under `src/app/content-page/store/media-items`, run:

```bash
ng test --watch=false --no-progress --browsers=ChromeHeadless --code-coverage --include=src/app/content-page/store/media-items
```

### Running end-to-end tests

For end-to-end (e2e) testing, run:

```bash
ng e2e
```

Angular CLI does not come with an end-to-end testing framework by default. You can choose one that suits your needs.

### Additional Resources

For more information on using the Angular CLI, including detailed command references, visit the [Angular CLI Overview and Command Reference](https://angular.dev/tools/cli) page.

## Deployment

- If you are deploying to Netlify, refer to the docs [here](./docs/deploying_to_netlify.md)

## Usage

Please note that this project is used for educational purposes and is not intended to be used commercially. We are not liable for any damages/changes done by this project.

## Credits

Emilio Kartono, who made the entire project.

UX Library provided by Daisy UI.

Icons provided by <https://heroicons.com>.

## License

This project is protected under the GNU licence. Please refer to the root project's LICENSE.txt for more information.
