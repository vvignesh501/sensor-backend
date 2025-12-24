# -*- coding: utf-8 -*-
"""
OpenTelemetry Tracing Configuration
Distributed tracing for microservices with Jaeger
"""

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
import logging

logger = logging.getLogger(__name__)


def setup_tracing(service_name: str, jaeger_host: str = "jaeger", jaeger_port: int = 6831):
    """
    Setup OpenTelemetry tracing with Jaeger exporter
    
    Args:
        service_name: Name of the service (e.g., "api-gateway", "sensor-service")
        jaeger_host: Jaeger agent hostname
        jaeger_port: Jaeger agent port
    """
    
    # Create resource with service information
    resource = Resource.create({
        "service.name": service_name,
        "service.version": "1.0.0",
        "deployment.environment": "production"
    })
    
    # Create Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=jaeger_host,
        agent_port=jaeger_port,
    )
    
    # Create tracer provider
    tracer_provider = TracerProvider(resource=resource)
    
    # Add span processor with Jaeger exporter
    span_processor = BatchSpanProcessor(jaeger_exporter)
    tracer_provider.add_span_processor(span_processor)
    
    # Set global tracer provider
    trace.set_tracer_provider(tracer_provider)
    
    logger.info(f"✓ OpenTelemetry tracing initialized for {service_name}")
    logger.info(f"  Jaeger endpoint: {jaeger_host}:{jaeger_port}")
    
    return trace.get_tracer(__name__)


def instrument_fastapi(app):
    """
    Instrument FastAPI application with OpenTelemetry
    Automatically traces all HTTP requests
    """
    FastAPIInstrumentor.instrument_app(app)
    logger.info("✓ FastAPI instrumented for tracing")


def instrument_requests():
    """
    Instrument requests library for tracing HTTP calls
    Automatically traces outgoing HTTP requests
    """
    RequestsInstrumentor().instrument()
    logger.info("✓ Requests library instrumented for tracing")


def instrument_sqlalchemy(engine):
    """
    Instrument SQLAlchemy for tracing database queries
    """
    SQLAlchemyInstrumentor().instrument(engine=engine)
    logger.info("✓ SQLAlchemy instrumented for tracing")


def instrument_redis(client):
    """
    Instrument Redis for tracing cache operations
    """
    RedisInstrumentor().instrument(redis_client=client)
    logger.info("✓ Redis instrumented for tracing")


def get_current_span():
    """Get the current active span"""
    return trace.get_current_span()


def add_span_attributes(**attributes):
    """
    Add custom attributes to current span
    
    Example:
        add_span_attributes(user_id="123", action="create_sensor")
    """
    span = get_current_span()
    for key, value in attributes.items():
        span.set_attribute(key, value)


def add_span_event(name: str, attributes: dict = None):
    """
    Add an event to current span
    
    Example:
        add_span_event("cache_hit", {"key": "sensor:123"})
    """
    span = get_current_span()
    span.add_event(name, attributes=attributes or {})


def record_exception(exception: Exception):
    """Record an exception in the current span"""
    span = get_current_span()
    span.record_exception(exception)
    span.set_status(trace.Status(trace.StatusCode.ERROR, str(exception)))
