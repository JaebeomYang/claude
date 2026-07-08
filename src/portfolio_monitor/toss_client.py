"""Client for the Toss Invest Open API.

NOTE: The exact auth flow and endpoint paths below could not be verified
against https://developers.tossinvest.com/docs (outbound network access to
that host was blocked in the environment this was written in). The paths
are marked with CONFIRM comments -- update them from the real docs before
relying on this in production. The public interface (get_access_token,
get_holdings) is intentionally stable so callers don't need to change when
the endpoints are corrected.
"""
import time
from dataclasses import dataclass

import requests

from .config import TossConfig


class TossApiError(RuntimeError):
    pass


@dataclass(frozen=True)
class Holding:
    ticker: str
    name: str
    quantity: float
    avg_price: float
    current_price: float
    change_pct: float
    volume: int


class TossClient:
    def __init__(self, config: TossConfig, session: requests.Session | None = None):
        self._config = config
        self._session = session or requests.Session()
        self._token = config.access_token
        self._token_expires_at = 0.0

    def _ensure_token(self) -> str:
        if self._token and time.time() < self._token_expires_at:
            return self._token
        if not self._config.client_id or not self._config.client_secret:
            if self._config.access_token:
                return self._config.access_token
            raise TossApiError(
                "No Toss access token available and no client_id/client_secret "
                "configured to request one."
            )
        # CONFIRM: real token endpoint + grant_type against Toss Open API docs.
        resp = self._session.post(
            f"{self._config.base_url}/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self._config.client_id,
                "client_secret": self._config.client_secret,
            },
            timeout=10,
        )
        if resp.status_code != 200:
            raise TossApiError(f"Token request failed: {resp.status_code} {resp.text}")
        payload = resp.json()
        self._token = payload["access_token"]
        self._token_expires_at = time.time() + float(payload.get("expires_in", 3600)) - 60
        return self._token

    def get_holdings(self) -> list[Holding]:
        token = self._ensure_token()
        # CONFIRM: real holdings/positions endpoint + response shape.
        resp = self._session.get(
            f"{self._config.base_url}/v1/accounts/holdings",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if resp.status_code != 200:
            raise TossApiError(f"Holdings request failed: {resp.status_code} {resp.text}")
        items = resp.json().get("holdings", [])
        return [
            Holding(
                ticker=item["ticker"],
                name=item.get("name", item["ticker"]),
                quantity=float(item["quantity"]),
                avg_price=float(item["avgPrice"]),
                current_price=float(item["currentPrice"]),
                change_pct=float(item["changeRate"]),
                volume=int(item.get("volume", 0)),
            )
            for item in items
        ]
