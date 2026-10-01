import logging
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger("finrecon.nova_client")


class NovaClient:
    """
    Server-side client for the Nova AI API (FIN-26 Financial Track Hackathon).
    
    Security & Architecture Rules:
    - API key is NEVER exposed to frontend, client responses, or logs.
    - Uses Bearer token authentication over TLS.
    - Handles timeouts (default 15s) and connection failures gracefully.
    - When unconfigured or unreachable, returns None to allow clean deterministic fallback.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.api_key = api_key if api_key is not None else settings.NOVA_API_KEY
        self.base_url = (base_url or settings.NOVA_API_BASE_URL).rstrip("/")
        self.timeout = timeout if timeout is not None else settings.NOVA_TIMEOUT_SECONDS

    @property
    def is_configured(self) -> bool:
        """Returns True only if an API key is non-empty."""
        return bool(self.api_key and self.api_key.strip())

    async def generate_explanation(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float = 0.1,
    ) -> Optional[str]:
        """
        Sends a controlled reconciliation evidence prompt to Nova.
        Returns the text response, or None if unconfigured / error occurs.
        """
        if not self.is_configured:
            logger.info("Nova API key not configured. Using deterministic explanation fallback.")
            return None

        endpoint = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json",
            "User-Agent": "FinRecon-Finance-Assistant/1.0",
        }

        payload = {
            "model": "nova-finance",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": 1500,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

                # Extract response text across common standard payload schemas
                if "choices" in data and len(data["choices"]) > 0:
                    choice = data["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        return choice["message"]["content"]
                    if "text" in choice:
                        return choice["text"]
                if "response" in data:
                    return str(data["response"])
                if "content" in data:
                    return str(data["content"])

                logger.warning("Nova response received but format was unexpected: %s", list(data.keys()))
                return None

        except httpx.TimeoutException:
            logger.warning("Nova API request timed out after %s seconds. Engaging fallback.", self.timeout)
            return None
        except httpx.HTTPStatusError as e:
            # Mask status and never print URL query/headers that might leak secrets
            logger.warning("Nova API HTTP error status code: %s. Engaging fallback.", e.response.status_code)
            return None
        except httpx.RequestError as e:
            logger.warning("Nova API connection network error. Engaging fallback.")
            return None
        except Exception as e:
            logger.error("Unexpected error contacting Nova API. Engaging fallback.")
            return None
