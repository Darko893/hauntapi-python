<div align="center">

<img src="https://hauntapi.com/favicon-192x192.png" width="76" alt="Haunt" />

# hauntapi

**Web extraction for AI agents.** Turn any permitted public web page into clean JSON or Markdown with one call, as a plain client or a LangChain, LlamaIndex, or CrewAI tool.

[![PyPI](https://img.shields.io/pypi/v/hauntapi?color=1f6feb)](https://pypi.org/project/hauntapi/)
[![Python](https://img.shields.io/pypi/pyversions/hauntapi)](https://pypi.org/project/hauntapi/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://opensource.org/licenses/MIT)

[Website](https://hauntapi.com) &middot; [Docs](https://hauntapi.com/docs) &middot; [Get a free key](https://hauntapi.com/?utm_source=github&utm_medium=readme&utm_campaign=hauntapi_sdk#signup) &middot; [MCP server](https://github.com/Darko893/mcp-server)

</div>

---

Haunt reads a public page and hands your agent structured data back. When a page is blocked, login-walled, CAPTCHA-gated, or too thin to trust, it returns an honest machine-readable error instead of fabricated data, so your agent can retry, switch source, skip, or ask a human.

Free tier: 1,000 credits a month, no card.

## Install

```bash
pip install hauntapi
```

## Quick start

```python
from hauntapi import Haunt

haunt = Haunt("your_api_key")          # or set HAUNT_API_KEY
result = haunt.extract("https://example.com/product", "product name and price")

if result.success:
    print(result.data)                 # {"name": "...", "price": "..."}
else:
    print(result.error_code)           # access_denied, login_required, not_found, ...
```

Markdown for RAG, notes, or `.md` files:

```python
result = haunt.extract("https://example.com/docs", "the page content",
                       response_format="markdown")
```

## Use it as an agent tool

The same client, wired into the framework you already use. Lazy imports, so you only need the one you install.

**LangChain**
```python
from hauntapi import langchain_tool
tools = [langchain_tool()]
```

**LlamaIndex**
```python
from hauntapi import llamaindex_tool
tools = [llamaindex_tool()]
```

**CrewAI**
```python
from crewai import Agent
from hauntapi import crewai_tool
researcher = Agent(role="Researcher", tools=[crewai_tool()])
```

Need the framework installed too? `pip install "hauntapi[langchain]"` (or `llamaindex`, `crewai`).

## Why honest failure matters for agents

An agent that receives fabricated data from a blocked page acts on garbage and cannot tell. Haunt returns error codes like `access_denied`, `login_required`, `captcha_required`, and `not_found`, so your agent branches on reality instead of a hallucination.

## Also in the box

- `haunt.extract_batch([...])` for many URLs in one call
- `haunt.extract_auth(...)` for pages you are allowed to access with your own headers
- `haunt.usage()` for remaining credits
- Full REST and MCP docs: https://hauntapi.com/docs

MIT licensed.
