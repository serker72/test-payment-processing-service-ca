from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def initialize_telemetry(project_info: dict, collector_host: str, collector_port: int):
    resource = Resource(attributes={"service.name": project_info["name"], "service.version": project_info["version"]})
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=f"http://{collector_host}:{collector_port}/v1/traces"))
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer(project_info["name"])
    return tracer
