"""S0 step 5: list available Gemini models."""
from assurance.env import api_key
from google import genai

c = genai.Client(api_key=api_key())
gem = sorted(m.name for m in c.models.list() if "gemini" in m.name)
for n in gem:
    print(n)
print(f"\n{len(gem)} gemini models total")
