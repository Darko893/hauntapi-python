import unittest
from typing import Any, cast

from hauntapi import Haunt, QuotaExceededError, _quota_error_message


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.posts = []
        self.closed = False

    def post(self, path, json):
        self.posts.append((path, json))
        return self.response

    def get(self, path):
        return self.response

    def close(self):
        self.closed = True


class HauntSdkTests(unittest.TestCase):
    def test_extract_sends_optional_response_format_device_and_js_scenario(self):
        fake = FakeClient(
            FakeResponse(
                payload={
                    "success": True,
                    "data": {"title": "Example"},
                    "credits_remaining": 998,
                    "trace": {"fetch": {"source": "playwright"}},
                }
            )
        )
        client = Haunt(api_key="haunt_test")
        client._client = cast(Any, fake)

        result = client.extract(
            url="https://example.com",
            prompt="Extract the title",
            response_format="markdown",
            device="mobile",
            js_scenario=[{"action": "scroll", "pixels": 400}],
        )

        self.assertTrue(result.success)
        self.assertEqual(result.data, {"title": "Example"})
        self.assertEqual(result.credits_remaining, 998)
        self.assertEqual(
            fake.posts,
            [
                (
                    "/v1/extract",
                    {
                        "url": "https://example.com",
                        "prompt": "Extract the title",
                        "response_format": "markdown",
                        "device": "mobile",
                        "js_scenario": [{"action": "scroll", "pixels": 400}],
                    },
                )
            ],
        )

    def test_extract_omits_optional_fields_when_not_provided(self):
        fake = FakeClient(FakeResponse(payload={"success": True, "data": {}}))
        client = Haunt(api_key="haunt_test")
        client._client = cast(Any, fake)

        client.extract(url="https://example.com", prompt="Extract the title")

        self.assertEqual(fake.posts, [("/v1/extract", {"url": "https://example.com", "prompt": "Extract the title"})])

    def test_quota_error_message_uses_remaining_and_used_separately(self):
        message = _quota_error_message(
            {
                "error": "Quota exceeded",
                "credits_remaining": 0,
                "credits_used_this_month": 1000,
                "credits_reserved_this_month": 2,
                "monthly_credits": 1000,
                "upgrade_url": "https://hauntapi.com/#pricing",
            }
        )

        self.assertIn("remaining=0", message)
        self.assertIn("used=1000", message)
        self.assertIn("reserved=2", message)
        self.assertIn("monthly_credits=1000", message)
        self.assertNotIn("remaining=1000", message)

    def test_extract_raises_quota_error_with_useful_message(self):
        fake = FakeClient(
            FakeResponse(
                status_code=429,
                payload={
                    "error": "Rate limit exceeded",
                    "credits_remaining": 0,
                    "credits_used_this_month": 1000,
                    "monthly_credits": 1000,
                },
            )
        )
        client = Haunt(api_key="haunt_test")
        client._client = cast(Any, fake)

        with self.assertRaises(QuotaExceededError) as ctx:
            client.extract(url="https://example.com", prompt="Extract the title")

        self.assertIn("remaining=0", str(ctx.exception))
        self.assertIn("used=1000", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
