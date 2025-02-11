# Setting up Tracer with Graphana Cloud

## Description

This document outlines the steps to set up and send OLTP traces to Graphana Cloud. This document comes from [graphana's original docs](https://grafana.com/docs/grafana-cloud/send-data/otlp/send-data-otlp/?utm_source=chatgpt.com#manual-opentelemetry-setup-for-advanced-users).

<https://grafana.com/orgs/goldfishsnailgoatrat/hosted-traces/1120311#sending-traces>

## Steps

### Setting up the app

1. Go to <https://grafana.com> and create a new account (free tier works)
2. Once you're signed in, go to <https://grafana.com/auth/sign-in/?src=chatgpt.com>
3. In your organization, click on `Details`
4. Scroll down, and you will see the endpoint to send OLTP signals. Copy this endpoint.
5. Scroll down, and you will see your API key. If not, create one. Copy your API key.
6. In your `.env` file, enable tracer and put the endpoint from step (4) and the api key from step (5) in the file like:

    ```env
    ...
    TRACER_ENABLED="true"
    TRACER_OTLP_ENDPOINT="<Your OLTP endpoint from step 4>"
    TRACER_OTLP_ENDPOINT="<Your OLTP api key from step 5>"
    ```

7. You're done! Launch your web api, and any incoming requests will send traces to Graphana Cloud.
