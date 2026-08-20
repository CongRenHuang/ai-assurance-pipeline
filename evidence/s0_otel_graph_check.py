"""S0 step 6: confirm OpenInference instrumentor can instrument graph workflow."""
from assurance.env import load
load()

from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from openinference.instrumentation.google_adk import GoogleADKInstrumentor

provider = trace_sdk.TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
GoogleADKInstrumentor().instrument(tracer_provider=provider)
print("instrumentor loaded")

from google.adk.workflow import Workflow, Edge, FunctionNode, START, DEFAULT_ROUTE


def classify(text: str) -> str:
    return "R0"


node = FunctionNode(func=classify, name="classify")
wf = Workflow(name="s0_probe", edges=[(START, node)])
print("graph workflow constructed under instrumentation")
print("   nodes:", [n.name for n in wf.graph.nodes] if hasattr(wf, "graph") else "n/a")
