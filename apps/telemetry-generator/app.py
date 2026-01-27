"""
Simple Telemetry Generator
Produces metrics, logs, and traces for testing observability stack
"""
import logging
import random
import time
from flask import Flask, jsonify
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

# Configuration
OTEL_ENDPOINT = "otel-collector:4317"
SERVICE_NAME = "telemetry-generator"

# Initialize OpenTelemetry components
resource = Resource.create({"service.name": SERVICE_NAME})

# Traces
trace_provider = TracerProvider(resource=resource)
trace_provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True))
)
trace.set_tracer_provider(trace_provider)
tracer = trace.get_tracer(__name__)

# Metrics
metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint=OTEL_ENDPOINT, insecure=True)
)
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter(__name__)

# Create custom metrics
request_counter = meter.create_counter(
    "requests_total",
    description="Total number of requests",
    unit="1"
)
processing_time = meter.create_histogram(
    "processing_duration_seconds",
    description="Time taken to process requests",
    unit="s"
)

# Logs
log_provider = LoggerProvider(resource=resource)
log_provider.add_log_record_processor(
    BatchLogRecordProcessor(OTLPLogExporter(endpoint=OTEL_ENDPOINT, insecure=True))
)
handler = LoggingHandler(level=logging.INFO, logger_provider=log_provider)
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)

@app.route("/")
def index():
    """Health check endpoint."""
    return jsonify({
        "service": SERVICE_NAME,
        "status": "healthy",
        "endpoints": ["/", "/generate", "/error", "/slow"]
    })

@app.route("/generate")
def generate():
    """Generate telemetry: trace, logs, and metrics."""
    with tracer.start_as_current_span("generate_telemetry") as span:
        start_time = time.time()
        
        # Add span attributes
        operation_id = random.randint(1000, 9999)
        span.set_attribute("operation.id", operation_id)
        span.set_attribute("operation.type", "generate")
        
        # Generate logs
        logger.info(
            f"Processing request {operation_id}",
            extra={"operation.id": operation_id, "status": "started"}
        )
        
        # Simulate work
        duration = random.uniform(0.01, 0.1)
        time.sleep(duration)
        
        # Record metrics
        request_counter.add(1, {"endpoint": "/generate", "status": "success"})
        processing_time.record(duration, {"endpoint": "/generate"})
        
        logger.info(
            f"Request {operation_id} completed",
            extra={"operation.id": operation_id, "status": "completed", "duration": duration}
        )
        
        return jsonify({
            "operation_id": operation_id,
            "duration": duration,
            "trace_id": format(span.get_span_context().trace_id, '032x'),
            "span_id": format(span.get_span_context().span_id, '016x')
        })

@app.route("/error")
def generate_error():
    """Generate an error trace and log."""
    with tracer.start_as_current_span("error_endpoint") as span:
        span.set_attribute("error", True)
        logger.error("Intentional error generated for testing")
        request_counter.add(1, {"endpoint": "/error", "status": "error"})
        
        return jsonify({"error": "Test error"}), 500

@app.route("/slow")
def slow_request():
    """Generate a slow request for latency testing."""
    with tracer.start_as_current_span("slow_request") as span:
        start_time = time.time()
        duration = random.uniform(1.0, 3.0)
        
        span.set_attribute("duration", duration)
        logger.warning(f"Slow request detected: {duration:.2f}s")
        
        time.sleep(duration)
        
        request_counter.add(1, {"endpoint": "/slow", "status": "success"})
        processing_time.record(duration, {"endpoint": "/slow"})
        
        return jsonify({"duration": duration})

if __name__ == "__main__":
    logger.info(f"{SERVICE_NAME} starting up")
    app.run(host="0.0.0.0", port=5000, debug=False)
