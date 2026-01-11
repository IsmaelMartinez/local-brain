"""OpenTelemetry tracing support for Local Brain.

Provides optional OTEL tracing integration via Smolagents instrumentor.
When enabled, captures:
- Agent runs (CodeAgent.run)
- Individual steps (Step 1, Step 2, ...)
- LLM calls with token counts
- Tool calls with inputs/outputs
"""

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Track if tracing is enabled
_tracing_enabled = False


def setup_tracing(
    console_output: bool = True, jaeger_endpoint: str = "http://localhost:4318/v1/traces"
) -> bool:
    """Enable OTEL tracing for Smolagents.

    Smolagents captures everything automatically once instrumented:
    - Agent execution spans
    - LLM calls with token counts
    - Tool invocations with inputs/outputs

    Args:
        console_output: If True, export spans to console (default).
                       Useful for debugging. Set False to disable.
        jaeger_endpoint: HTTP endpoint for Jaeger OTEL receiver.
                        Default assumes Jaeger running locally on port 4318.
                        Set to None to skip Jaeger export.

    Returns:
        True if tracing was enabled, False if dependencies missing.

    Example:
        if trace_flag:
            if setup_tracing():
                click.echo("🔍 Tracing enabled - view at http://localhost:16686")
            else:
                click.echo("⚠️  Tracing unavailable (missing dependencies)")

    Note:
        For Jaeger visualization, run locally with:
        docker run -p 16686:16686 -p 4318:4318 jaegertracing/all-in-one
    """
    global _tracing_enabled

    if _tracing_enabled:
        return True

    try:
        from openinference.instrumentation.smolagents import SmolagentsInstrumentor
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
            ConsoleSpanExporter,
        )

        # Create and set tracer provider
        tracer_provider = TracerProvider()
        trace.set_tracer_provider(tracer_provider)

        # Add console exporter for debugging
        if console_output:
            tracer_provider.add_span_processor(
                BatchSpanProcessor(ConsoleSpanExporter())
            )

        # Add Jaeger exporter for visualization
        if jaeger_endpoint:
            try:
                from opentelemetry.exporter.trace.otlp.proto.http.trace_exporter import (
                    OTLPSpanExporter,
                )

                jaeger_exporter = OTLPSpanExporter(endpoint=jaeger_endpoint)
                tracer_provider.add_span_processor(
                    BatchSpanProcessor(jaeger_exporter)
                )
            except ImportError:
                print(
                    "Note: Jaeger export not available. Install with: "
                    "pip install opentelemetry-exporter-otlp",
                    file=sys.stderr,
                )

        # Instrument Smolagents - this captures agent runs, steps, LLM calls, tools
        SmolagentsInstrumentor().instrument(tracer_provider=tracer_provider)

        _tracing_enabled = True
        return True

    except ImportError as e:
        # Missing dependencies - tracing is optional
        print(
            f"Warning: Tracing dependencies not installed ({e}). "
            "Install with: pip install openinference-instrumentation-smolagents "
            "opentelemetry-sdk",
            file=sys.stderr,
        )
        return False


def is_tracing_enabled() -> bool:
    """Check if tracing is currently enabled.

    Returns:
        True if setup_tracing() was called successfully.
    """
    return _tracing_enabled


def get_tracer(name: str = "local-brain"):
    """Get a tracer for manual span creation.

    Args:
        name: Name for the tracer (default: "local-brain").

    Returns:
        A tracer instance, or a no-op tracer if tracing not enabled.

    Example:
        tracer = get_tracer()
        with tracer.start_as_current_span("custom_operation"):
            do_something()
    """
    try:
        from opentelemetry import trace

        return trace.get_tracer(name)
    except ImportError:
        # Return a no-op tracer
        class NoOpTracer:
            def start_as_current_span(self, name, **kwargs):
                from contextlib import nullcontext

                return nullcontext()

        return NoOpTracer()
