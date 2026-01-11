# ADR-006: OpenTelemetry/Jaeger Tracing Integration

**Status:** Accepted
**Date:** 2025-01-11

## Context

Local Brain uses Smolagents for agent execution, which includes built-in OpenTelemetry instrumentation via the `openinference-instrumentation-smolagents` package. We needed a way to visualize agent execution for debugging and understanding model behavior, especially when comparing different models like qwen3:30b vs qwen3-coder:30b.

## Decision

Integrate OpenTelemetry tracing with Jaeger as the visualization backend, making it an optional feature with graceful degradation when dependencies aren't installed.

### Implementation

The tracing module (`local_brain/tracing.py`) provides:

1. **Optional OTEL Setup** - The `setup_tracing()` function returns True/False to indicate success, allowing the CLI to show appropriate messages without crashing if dependencies are missing.

2. **Smolagents Instrumentation** - Uses `SmolagentsInstrumentor` from openinference to automatically capture:
   - Agent execution spans (`CodeAgent.run`)
   - Individual step spans (Step 1, Step 2, ...)
   - LLM calls with token counts
   - Tool invocations with inputs/outputs

3. **Jaeger OTLP Export** - Spans are exported to Jaeger via the OTLP HTTP protocol (port 4318), with console output available for debugging without Jaeger.

4. **Service Naming** - Uses OTEL Resource with `service.name=local-brain` so traces appear correctly in Jaeger's service dropdown.

### Why Jaeger

We chose Jaeger as the recommended visualization tool for several reasons. It's available as a single Docker container (`jaegertracing/all-in-one`) with no configuration required. It natively supports OTLP which is the standard OTEL export protocol. The waterfall timeline view is ideal for understanding nested agent/step/tool execution. It's also open source with a mature ecosystem and good documentation.

### Dependency Strategy

Tracing dependencies are optional (`pip install local-brain[tracing]`) to keep the base installation lightweight. When dependencies are missing, the CLI shows a helpful message and continues normally. This follows the principle that observability features should enhance but never block core functionality.

## Consequences

### Positive
- Full visibility into agent execution without code changes
- Token usage tracking per step helps identify expensive operations
- Debugging model comparison tests becomes straightforward
- Industry-standard tooling (OTEL/Jaeger) means familiar workflows

### Negative
- Requires Docker for Jaeger (or alternative OTEL backend)
- Additional optional dependencies (~15MB)
- Console output mode is verbose and hard to read for complex traces

### Related Decisions
- ADR-007 (Debug Mode) complements this by providing real-time step output without requiring Jaeger setup
