"""Client for the Toss Invest Open API (https://openapi.tossinvest.com).

Endpoints and auth flow are taken from the official OpenAPI spec (v1.2.2):
- POST /oauth2/token: OAuth2 client_credentials grant (form-urlencoded).
  One valid access token per client; reissuing invalidates the previous one.
- GET /api/v1/accounts: list of brokerage accounts (accountSeq, accountNo).
- GET /api/v1/holdings: holdings for an account (X-Tossinvest-Account header).
- GET /api/v1/candles: daily/minute OHLCV, used here to get volume history
  since /holdings itself does not report volume.
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
    market_country: str
    currency: str
    quantity: float
    last_price: float
    avg_price: float
    change_pct: float  # daily change, in percent (e.g. 3.5 == +3.5%)
    profit_loss_rate: float  # in percent


@dataclass(frozen=True)
class Candle:
    timestamp: str
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float


class TossClient:
    def __init__(self, config: TossConfig, session: requests.Session | None = None):
        self._config = config
        self._session = session or requests.Session()
        self._token = config.access_token
        self._token_expires_at = 0.0
        self._account_seq: int | None = None

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
        self._token_expires_at = time.time() + float(payload["expires_in"]) - 60
        return self._token

    def _get(self, path: str, params: dict | None = None, account_seq: int | None = None):
        headers = {"Authorization": f"Bearer {self._ensure_token()}"}
        if account_seq is not None:
            headers["X-Tossinvest-Account"] = str(account_seq)
        resp = self._session.get(
            f"{self._config.base_url}{path}", headers=headers, params=params, timeout=10
        )
        if resp.status_code != 200:
            raise TossApiError(f"GET {path} failed: {resp.status_code} {resp.text}")
        return resp.json()["result"]

    def get_accounts(self) -> list[dict]:
        return self._get("/api/v1/accounts")

    def get_account_seq(self) -> int:
        if self._account_seq is None:
            accounts = self.get_accounts()
            if not accounts:
                raise TossApiError("No brokerage accounts found for this client.")
            self._account_seq = accounts[0]["accountSeq"]
        return self._account_seq

    def get_holdings(self) -> list[Holding]:
        result = self._get("/api/v1/holdings", account_seq=self.get_account_seq())
        return [
            Holding(
                ticker=item["symbol"],
                name=item["name"],
                market_country=item["marketCountry"],
                currency=item["currency"],
                quantity=float(item["quantity"]),
                last_price=float(item["lastPrice"]),
                avg_price=float(item["averagePurchasePrice"]),
                change_pct=float(item["dailyProfitLoss"]["rate"]) * 100,
                profit_loss_rate=float(item["profitLoss"]["rate"]) * 100,
            )
            for item in result["items"]
        ]

    def get_daily_candles(self, symbol: str, count: int = 15) -> list[Candle]:
        """Most-recent-first daily candles, per the API's pagination order."""
        result = self._get(
            "/api/v1/candles", params={"symbol": symbol, "interval": "1d", "count": count}
        )
        return [
            Candle(
                timestamp=c["timestamp"],
                open_price=float(c["openPrice"]),
                high_price=float(c["highPrice"]),
                low_price=float(c["lowPrice"]),
                close_price=float(c["closePrice"]),
                volume=float(c["volume"]),
            )
            for c in result["candles"]
        ]
