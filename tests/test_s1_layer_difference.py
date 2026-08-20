"""Proves Plugin layer (is not None) and Agent layer (truthy) short-circuit differently."""
import inspect
from google.adk.plugins import plugin_manager
from google.adk.flows.llm_flows import functions

pm = inspect.getsource(plugin_manager)
fn = inspect.getsource(functions)

print("Plugin layer short-circuit condition:")
for ln in pm.splitlines():
    if "is not None" in ln and "result" in ln:
        print("   ", ln.strip())

print("\nAgent layer short-circuit condition:")
for ln in fn.splitlines():
    if "if function_response:" in ln:
        print("   ", ln.strip())

print("\n-> Plugin uses `is not None` (empty dict blocks)")
print("-> Agent uses truthy (empty dict does not block)")
