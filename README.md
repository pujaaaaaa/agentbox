# ✈️ AgentBox

### The Local-First AI Flight Recorder
**Zero Dependencies. 100% Local SQLite. Zero Cloud Friction.**

AgentBox is a lightweight utility designed to intercept, track, and audit AI agent architectures (like Hugging Face `smolagents`) completely offline. 

### 📊 Advanced Analytics Included
* **Token Auditing:** Automatically harvests raw input/output token metrics from active frameworks.
* **Financial Cost Indexing:** Generates real-time financial run cost estimations down to fractional US dollars so you can audit cloud spend locally.

## 🚀 Quick Start

1. Drop `agentbox.py` into your project folder.
2. Wrap your agent function with the decorator:

```python
from agentbox import record_agent

@record_agent(name="My_Agent")
def run_ai():
    # Your agent code here
    return response



