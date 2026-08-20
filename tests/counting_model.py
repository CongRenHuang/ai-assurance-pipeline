"""Wraps the real model to count actual generate_content calls.

This is S2's source of evidence -- not response text, but a direct
count of API invocations.
"""
from google.adk.models.google_llm import Gemini

CALLS = {"generate_content": 0}


class CountingGemini(Gemini):
    async def generate_content_async(self, llm_request, stream=False):
        CALLS["generate_content"] += 1
        async for r in super().generate_content_async(llm_request, stream=stream):
            yield r


def reset():
    CALLS["generate_content"] = 0
