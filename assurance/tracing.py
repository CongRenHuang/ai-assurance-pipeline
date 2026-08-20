"""OpenInference tracing + assurance 專用 span 屬性。"""
from __future__ import annotations
import os
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor, ConsoleSpanExporter)

_provider: trace_sdk.TracerProvider | None = None
CAPTURED: list[dict] = []


class CapturingExporter(ConsoleSpanExporter):
    """同時輸出到 console 並保留在記憶體，供測試斷言。"""
    def export(self, spans):
        for s in spans:
            CAPTURED.append({
                "name": s.name,
                "attributes": dict(s.attributes or {}),
                "parent_id": s.parent.span_id if s.parent else None,
                "span_id": s.context.span_id,
            })
        return super().export(spans)


def setup(use_otlp: bool = False, endpoint: str | None = None):
    global _provider
    if _provider:
        return _provider
    _provider = trace_sdk.TracerProvider()

    if use_otlp:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter)
        ep = endpoint or os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:6006/v1/traces")
        _provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(ep)))
    else:
        _provider.add_span_processor(SimpleSpanProcessor(CapturingExporter()))

    from openinference.instrumentation.google_adk import GoogleADKInstrumentor
    GoogleADKInstrumentor().instrument(tracer_provider=_provider)
    trace.set_tracer_provider(_provider)
    return _provider


def tracer():
    return trace.get_tracer("assurance")


# ---- OpenInference span kind 常數 ----
SPAN_KIND = "openinference.span.kind"
GUARDRAIL = "GUARDRAIL"
EVALUATOR = "EVALUATOR"
CHAIN = "CHAIN"


@contextmanager
def guardrail_span(name: str, *, policy_id: str, risk_tier: str,
                   decision: str, plugin: str, plugin_index: int,
                   override_rejected: bool = False):
    """policy check span，標記為 GUARDRAIL。

    plugin / plugin_index 記錄「哪個 plugin、在鏈中第幾個位置」做出這個決定，
    讓 plugin 短路順序在 trace 上可查詢。
    """
    with tracer().start_as_current_span(name) as sp:
        sp.set_attribute(SPAN_KIND, GUARDRAIL)
        sp.set_attribute("assurance.policy_id", policy_id)
        sp.set_attribute("assurance.risk_tier", risk_tier)
        sp.set_attribute("assurance.decision", decision)
        sp.set_attribute("assurance.override_rejected", override_rejected)
        sp.set_attribute("assurance.plugin", plugin)
        sp.set_attribute("assurance.plugin_index", plugin_index)
        yield sp


@contextmanager
def evaluator_span(name: str, *, evaluation: str, score: float, status: str):
    """evaluation span，標記為 EVALUATOR。"""
    with tracer().start_as_current_span(name) as sp:
        sp.set_attribute(SPAN_KIND, EVALUATOR)
        sp.set_attribute("assurance.evaluation", evaluation)
        sp.set_attribute("assurance.score", score)
        sp.set_attribute("assurance.status", status)
        yield sp
