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


class Haunt:
    """Haunt API client.

    Args:
        api_key: Your Haunt API key (get one at https://hauntapi.com)
        base_url: API base URL (default: https://hauntapi.com)
        timeout: Request timeout in seconds (default: 120)
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://hauntapi.com",
        timeout: int = 120,
    ):
        self.api_key = api_key
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
    ) -> ExtractResult:
        """Extract structured data from a URL.

        Args:
            url: The URL to extract data from
            prompt: Describe what data you want in plain English

        Returns:
            ExtractResult with the extracted data as a dict

        Example:
            result = client.extract(
                url="https://example.com/products",
                prompt="Get all product names and prices"
            )
            print(result.data)
        """
        resp = self._client.post(
            "/v1/extract",
            json={"url": url, "prompt": prompt},
        )
        data = resp.json()

        if resp.status_code == 401:
            raise AuthenticationError("Invalid API key")
        if resp.status_code == 429:
            raise QuotaExceededError(
                f"Monthly quota exceeded. Remaining: {data.get('detail', {}).get('used', '?')}"
            )

        return ExtractResult(
            success=data.get("success", False),
            data=data.get("data"),
            error=data.get("error"),
            url=data.get("url"),
            latency_ms=data.get("latency_ms"),
            tokens_used=data.get("tokens_used"),
            credits_remaining=data.get("credits_remaining"),
        )

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
            raise QuotaExceededError("Monthly quota exceeded")

        return ExtractResult(
            success=data.get("success", False),
            data=data.get("data"),
            error=data.get("error"),
            url=data.get("url"),
            latency_ms=data.get("latency_ms"),
            tokens_used=data.get("tokens_used"),
            credits_remaining=data.get("credits_remaining"),
        )

    def extract_batch(
        self,
        urls: list[str],
        prompt: str,
    ) -> BatchResult:
        """Extract data from multiple URLs at once.

        Sends the same prompt to each URL. Each URL counts as one request.
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
