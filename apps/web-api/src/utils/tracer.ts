import { trace } from '@opentelemetry/api';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { registerInstrumentations } from '@opentelemetry/instrumentation';
import { ExpressInstrumentation } from '@opentelemetry/instrumentation-express';
import { HttpInstrumentation } from '@opentelemetry/instrumentation-http';
import { MongoDBInstrumentation } from '@opentelemetry/instrumentation-mongodb';
import { Resource } from '@opentelemetry/resources';
import {
  BatchSpanProcessor,
  ConsoleSpanExporter,
  SimpleSpanProcessor
} from '@opentelemetry/sdk-trace-base';
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';
import logger from './logger';

/**
 * Sets up tracer. Should be called once at the beginning of app launch.
 */
export function setupTracer(oltpEndpoint: string, oltpApiKey: string) {
  // Create a tracer provider with a resource that identifies your service
  const provider = new NodeTracerProvider({
    resource: new Resource({
      [SemanticResourceAttributes.SERVICE_NAME]: 'sharded-photos-drive-web-api'
    })
  });

  console.log(oltpEndpoint, oltpApiKey);

  // Configure the OTLP exporter
  const exporter = new OTLPTraceExporter({
    url: 'https://otlp-gateway-prod-us-west-0.grafana.net/otlp',
    headers: {
      Authorization:
        'Basic MTE2ODE5NzpnbGNfZXlKdklqb2lNVE0wTmpNME5DSXNJbTRpT2lKemRHRmpheTB4TVRZNE1UazNMVzkwYkhBdGQzSnBkR1V0YUdWb1pTSXNJbXNpT2lKSGVuSk1ZVFJIZVRBeldVSTJPREkwYVVRMFVqTjVNRTRpTENKdElqcDdJbklpT2lKd2NtOWtMWFZ6TFhkbGMzUXRNQ0o5ZlE9PQ=='
    }
  });

  // Add a span processor to send spans to the exporter
  const hehe = new SimpleSpanProcessor(exporter);
  provider.addSpanProcessor(hehe); // switch to BatchSpanProcessor for better performance.
  provider.addSpanProcessor(new BatchSpanProcessor(new ConsoleSpanExporter()));

  // Register the provider to begin tracing
  provider.register();

  // Register auto-instrumentations for Express, HTTP, and MongoDB.
  // These instrumentations automatically create spans for:
  //  • Incoming HTTP requests (Express)
  //  • Outgoing HTTP requests (external API calls via HTTP/HTTPS modules or libraries like Axios)
  //  • MongoDB queries (for common methods like find, insert, update, etc.)
  registerInstrumentations({
    instrumentations: [
      new ExpressInstrumentation(),
      new HttpInstrumentation(),
      new MongoDBInstrumentation({ enhancedDatabaseReporting: true })
    ]
  });

  const tracer = trace.getTracer('sharded-photos-drive-web-api');
  const span = tracer.startSpan('my-operation');
  // Your OLTP data processing logic here
  span.addEvent('data-processed', { key: 'value' });
  span.end();

  exporter.forceFlush();

  logger.info('OpenTelemetry tracer initialized.');
}
