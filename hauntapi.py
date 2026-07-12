"""
Haunt API Python SDK
Extract structured data from permitted public pages with one API call.

Usage:
    pip install hauntapi

    from hauntapi import Haunt

    client = Haunt(api_key="haunt_your_key")

    # Extract data
    result = client.extract(
        url="https://news.ycombinator.com",
        prompt="Get the top 5 story titles and their points"
    )

    print(result.data)
    # {"stories": [{"title": "...", "points": 572}, ...]}

    # Authenticated scraping
    result = client.extract_auth(
        url="https://portal.example.com/dashboard",
        prompt="Get all account balances",
        cookies={"session_id": "abc123"}
    )

    # Batch extraction
    results = client.extract_batch(
        urls=["https://site1.com", "https://site2.com"],
        prompt="Get the page title and meta description"
    )
"""

import os
import httpx
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class ExtractResult:
    """Result from an extraction request."""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    url: Optional[str] = None
    latency_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    credits_remaining: Optional[int] = None
    message: Optional[str] = None
    error_code: Optional[str] = None
    charged: Optional[bool] = None
    credits_used: Optional[int] = None
    mode: Optional[str] = None
    confidence: Optional[float] = None
    evidence: Optional[dict] = None
    trace: Optional[dict] = None

    def __repr__(self):
        if self.success:
            return f"<ExtractResult success=True data={self.data} remaining={self.credits_remaining}>"
        return f"<ExtractResult success=False error='{self.error}'>"


@dataclass
class BatchResult:
    """Result from a batch extraction request."""
    results: list = field(default_factory=list)
    total: int = 0
    successful: int = 0
    credits_remaining: Optional[int] = None

    def __repr__(self):
        return f"<BatchResult total={self.total} successful={self.successful} remaining={self.credits_remaining}>"


def _extract_result_from_data(data: dict) -> ExtractResult:
    """Build ExtractResult from the current Haunt response contract."""
    return ExtractResult(
        success=data.get("success", False),
        data=data.get("data"),
        error=data.get("error"),
        url=data.get("url"),
        latency_ms=data.get("latency_ms"),
        tokens_used=data.get("tokens_used"),
        credits_remaining=data.get("credits_remaining"),
        message=data.get("message"),
        error_code=data.get("error_code"),
        charged=data.get("charged"),
        credits_used=data.get("credits_used"),
        mode=data.get("mode"),
        confidence=data.get("confidence"),
        evidence=data.get("evidence"),
        trace=data.get("trace"),
    )


def _quota_error_message(data: dict) -> str:
    """Return a useful 429 message without mislabeling used credits as remaining."""
    detail = data.get("detail") if isinstance(data.get("detail"), dict) else {}
    source = {**detail, **data}
    message = source.get("message") or source.get("error") or "Monthly quota or rate limit exceeded"
    parts = [str(message)]
    if source.get("credits_remaining") is not None or source.get("remaining") is not None:
        parts.append(f"remaining={source.get('credits_remaining', source.get('remaining'))}")
    if source.get("used") is not None or source.get("credits_used_this_month") is not None:
        parts.append(f"used={source.get('used', source.get('credits_used_this_month'))}")
    if source.get("reserved") is not None or source.get("credits_reserved_this_month") is not None:
        parts.append(f"reserved={source.get('reserved', source.get('credits_reserved_this_month'))}")
    if source.get("monthly_credits") is not None or source.get("monthly_limit") is not None:
        parts.append(f"monthly_credits={source.get('monthly_credits', source.get('monthly_limit'))}")
    if source.get("upgrade_url"):
        parts.append(f"upgrade={source.get('upgrade_url')}")
    return "; ".join(parts)


class Haunt:
    """Haunt API client.

    Args:
        api_key: Your Haunt API key (get one at https://hauntapi.com)
        base_url: API base URL (default: https://hauntapi.com)
        timeout: Request timeout in seconds (default: 120)
    """

    def __init__(
        self,
        api_key: str = None,
        base_url: str = "https://hauntapi.com",
        timeout: int = 120,
    ):
        self.api_key = api_key or os.environ.get("HAUNT_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "No API key. Pass api_key or set HAUNT_API_KEY. "
                "Free key: https://hauntapi.com/#signup"
            )
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    def extract(
        self,
        url: str,
        prompt: str,
        response_format: Optional[str] = None,
        device: Optional[str] = None,
        js_scenario: Optional[list] = None,
    ) -> ExtractResult:
        """Extract structured data from a URL.

        Args:
            url: The URL to extract data from
            prompt: Describe what data you want in plain English
            response_format: Optional. "markdown"/"md" for clean page text, "raw_html"/"html", "json" (default), or "screenshot".
            device: Optional. "mobile" or "desktop" render profile (forces browser rendering).
            js_scenario: Optional (paid plans). Up to 10 scripted browser steps before extraction.

        Returns:
            ExtractResult with the extracted data as a dict

        Example:
            result = client.extract(
                url="https://example.com/products",
                prompt="Get all product names and prices"
            )
            print(result.data)
        """
        body: dict = {"url": url, "prompt": prompt}
        if response_format is not None:
            body["response_format"] = response_format
        if device is not None:
            body["device"] = device
        if js_scenario is not None:
            body["js_scenario"] = js_scenario
        resp = self._client.post(
            "/v1/extract",
            json=body,
        )
        data = resp.json()

        if resp.status_code == 401:
            raise AuthenticationError("Invalid API key")
        if resp.status_code == 429:
            raise QuotaExceededError(_quota_error_message(data))

        return _extract_result_from_data(data)

    def extract_auth(
        self,
        url: str,
        prompt: str,
        cookies: Optional[dict] = None,
        headers: Optional[dict] = None,
        raw_html: bool = False,
    ) -> ExtractResult:
        """Extract data from an authenticated/private page.

        Send cookies or headers to access pages behind login walls.
        Requires Pro or Scale plan.

        Args:
            url: The URL to extract data from
            prompt: Describe what data you want
            cookies: Dict of cookies to send (e.g. {"session": "abc123"})
            headers: Dict of custom headers (e.g. {"Authorization": "Bearer token"})
            raw_html: If True, return raw HTML instead of LLM extraction

        Returns:
            ExtractResult with the extracted data
        """
        payload = {
            "url": url,
            "prompt": prompt,
            "raw_html": raw_html,
        }
        if cookies:
            payload["cookies"] = cookies
        if headers:
            payload["headers"] = headers

        resp = self._client.post("/v1/extract/auth", json=payload)
        data = resp.json()

        if resp.status_code == 401:
            raise AuthenticationError("Invalid API key")
        if resp.status_code == 403:
            detail = data.get("detail", {})
            raise PlanRequiredError(
                f"{detail.get('error', 'Plan upgrade required')}. Current: {detail.get('current_plan', 'unknown')}"
            )
        if resp.status_code == 429:
            raise QuotaExceededError(_quota_error_message(data))

        return _extract_result_from_data(data)

    def extract_batch(
        self,
        urls: list[str],
        prompt: str,
    ) -> BatchResult:
        """Extract data from multiple URLs at once.

        Sends the same prompt to each URL. Each URL is billed as a normal structured extraction (2 credits, plus any large-page surcharge).
        Requires Scale plan.

        Args:
            urls: List of URLs (max 10)
            prompt: Describe what data you want from each page

        Returns:
            BatchResult with results for each URL
        """
        resp = self._client.post(
            "/v1/extract/batch",
            json={"urls": urls, "prompt": prompt},
        )
        data = resp.json()

        if resp.status_code == 401:
            raise AuthenticationError("Invalid API key")
        if resp.status_code == 403:
            raise PlanRequiredError("Batch extraction requires Scale plan")

        return BatchResult(
            results=data.get("results", []),
            total=data.get("total", 0),
            successful=data.get("successful", 0),
            credits_remaining=data.get("credits_remaining"),
        )

    def usage(self) -> dict:
        """Get your current usage and quota.

        Returns:
            Dict with plan, usage_this_month, monthly_limit, remaining
        """
        resp = self._client.get("/v1/extract/usage")
        return resp.json()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._client.close()

    def close(self):
        self._client.close()


class HauntError(Exception):
    """Base exception for Haunt API errors."""
    pass


class AuthenticationError(HauntError):
    """Invalid API key."""
    pass


class QuotaExceededError(HauntError):
    """Monthly request quota exceeded."""
    pass


class PlanRequiredError(HauntError):
    """Current plan doesn't support this feature."""
    pass


# ---------------------------------------------------------------------------
# Agent-framework tools. Same Haunt client, wired into LangChain, LlamaIndex,
# or CrewAI. Lazy imports, so you only need the framework you actually install.
# ---------------------------------------------------------------------------

def _tool_run(client, url, prompt):
    import json as _json
    result = client.extract(url, prompt)
    if not result.success:
        return _json.dumps({
            "error_code": result.error_code or "extraction_failed",
            "message": result.message or result.error or "extraction failed",
        })
    data = result.data
    return data if isinstance(data, str) else _json.dumps(data)


def langchain_tool(api_key=None, **kwargs):
    """Return a LangChain StructuredTool backed by Haunt. Requires langchain-core."""
    try:
        from langchain_core.tools import StructuredTool
        from pydantic import BaseModel, Field
    except ImportError as exc:  # pragma: no cover
        raise ImportError("Install langchain-core to use langchain_tool().") from exc
    client = Haunt(api_key=api_key, **kwargs)

    class _Args(BaseModel):
        url: str = Field(description="The public web page URL to extract from.")
        prompt: str = Field(description="Plain-language description of the data to return.")

    return StructuredTool.from_function(
        func=lambda url, prompt: _tool_run(client, url, prompt),
        name="haunt_extract",
        description=(
            "Extract structured data or clean text from a public web page. Input a "
            "URL and a plain-language prompt of what to return. Returns JSON, or an "
            "honest error_code (access_denied, login_required, not_found) instead of "
            "made-up data when the page cannot be read."
        ),
        args_schema=_Args,
    )


def llamaindex_tool(api_key=None, **kwargs):
    """Return a LlamaIndex FunctionTool backed by Haunt. Requires llama-index-core."""
    try:
        from llama_index.core.tools import FunctionTool
    except ImportError as exc:  # pragma: no cover
        raise ImportError("Install llama-index-core to use llamaindex_tool().") from exc
    client = Haunt(api_key=api_key, **kwargs)

    def haunt_extract(url: str, prompt: str) -> str:
        """Extract structured data or clean text from a public web page URL and prompt."""
        return _tool_run(client, url, prompt)

    return FunctionTool.from_defaults(fn=haunt_extract, name="haunt_extract")


def crewai_tool(api_key=None, **kwargs):
    """Return a CrewAI tool backed by Haunt. Requires crewai."""
    try:
        from crewai.tools import tool
    except ImportError as exc:  # pragma: no cover
        raise ImportError("Install crewai to use crewai_tool().") from exc
    client = Haunt(api_key=api_key, **kwargs)

    @tool("Haunt web extraction")
    def haunt_extract(url: str, prompt: str) -> str:
        """Extract structured data or clean text from a public web page URL and prompt."""
        return _tool_run(client, url, prompt)

    return haunt_extract
