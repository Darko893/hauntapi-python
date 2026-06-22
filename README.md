# hauntapi

Python SDK for [Haunt API](https://hauntapi.com) — extract structured data from permitted public pages with one API call.

## Install

```bash
pip install hauntapi
```

## Quick Start

```python
from hauntapi import Haunt

client = Haunt(api_key="haunt_your_key")

# Extract data from any URL
result = client.extract(
    url="https://news.ycombinator.com",
    prompt="Get the top 5 story titles and their points"
)

print(result.data)
# {"stories": [{"title": "...", "points": 572}, ...]}

print(result.credits_remaining)
# 998

# Get usage info
print(client.usage())
# {"plan": "free", "remaining": 998, "monthly_limit": 1000}

# Optional response modes and browser-rendering controls
markdown = client.extract(
    url="https://example.com",
    prompt="Return the main page content as Markdown",
    response_format="markdown",
)

mobile = client.extract(
    url="https://example.com/products",
    prompt="Extract product names and prices",
    device="mobile",
)

# Paid plans only: run bounded browser steps before extraction
result = client.extract(
    url="https://example.com/products",
    prompt="Extract visible product names and prices",
    js_scenario=[{"action": "scroll", "pixels": 800}],
)
```

## Features

- **`extract(url, prompt, response_format=..., device=..., js_scenario=...)`** — Extract structured data, Markdown, raw HTML, screenshots, or render with a mobile/desktop browser profile
- **`extract_auth(url, prompt, cookies=..., headers=...)`** — Extract from authenticated/private pages
- **`extract_batch(urls, prompt)`** — Extract from multiple URLs at once
- **`usage()`** — Check your quota and plan

## Error Handling

```python
from hauntapi import Haunt, AuthenticationError, QuotaExceededError

client = Haunt(api_key="your_key")

try:
    result = client.extract(url="https://example.com", prompt="Get the title")
except AuthenticationError:
    print("Invalid API key")
except QuotaExceededError:
    print("Monthly quota exceeded")
```

## Pricing

- **Free**: 1,000 credits/month, no credit card
- **Starter**: £19/month for 10,000 credits
- **Pro**: £49/month for 30,000 credits plus authenticated extraction
- **Scale**: £99/month for 80,000 credits plus batch extraction

Get your API key at [hauntapi.com](https://hauntapi.com).

## Links

- Docs: https://hauntapi.com/docs
- MCP Server: https://github.com/Darko893/mcp-server
- API: https://hauntapi.com
