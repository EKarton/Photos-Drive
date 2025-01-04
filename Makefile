CLI_CLIENT_DIR = ./apps/cli-client
WEB_API_DIR = ./apps/web-api
WEB_UI_DIR = ./apps/web-ui

# Default target
.PHONY: all
all: install build

# Install all application dependencies
.PHONY: install
build: install-cli-client install-web-api install-web-ui 

# Install cli-client dependencies
.PHONY: install-cli-client
install-cli-client:
	cd ${CLI_CLIENT_DIR} && poetry install

# Install web api dependencies
.PHONY: install-web-api
install-web-api:
	cd ${WEB_API_DIR} && pnpm install

# Install web-ui dependencies
.PNONY: install-web-ui
install-web-ui:
	cd ${WEB_UI_DIR} && npm install


# Build all applications
.PHONY: build
build: build-web-api build-web-ui 

# Build web api
.PHONY: build-web-api
build-web-api:
	cd ${WEB_API_DIR} && pnpm run build

# Building web-ui
.PNONY: build-web-ui
build-web-ui:
	cd ${WEB_UI_DIR} && ng build
