"""End-to-end smoke test for TossClient against a fake HTTP session.

Real network access to openapi.tossinvest.com isn't available in this
environment, so this exercises the full auth -> account -> holdings ->
candles flow against canned responses shaped exactly like the official
OpenAPI examples, instead of skipping verification entirely.
"""
from portfolio_monitor.config import TossConfig
from portfolio_monitor.toss_client import TossClient


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self):
        self.requests = []

    def post(self, url, data=None, timeout=None):
        self.requests.append(("POST", url, data))
        assert url.endswith("/oauth2/token")
        assert data["grant_type"] == "client_credentials"
        assert data["client_id"] == "test-client-id"
        assert data["client_secret"] == "test-client-secret"
        return FakeResponse(
            200, {"access_token": "fake-token", "token_type": "Bearer", "expires_in": 86400}
        )

    def get(self, url, headers=None, params=None, timeout=None):
        self.requests.append(("GET", url, headers, params))
        assert headers["Authorization"] == "Bearer fake-token"

        if url.endswith("/api/v1/accounts"):
            return FakeResponse(
                200,
                {"result": [{"accountNo": "12345678901", "accountSeq": 1, "accountType": "BROKERAGE"}]},
            )

        if url.endswith("/api/v1/holdings"):
            assert headers["X-Tossinvest-Account"] == "1"
            return FakeResponse(
                200,
                {
                    "result": {
                        "items": [
                            {
                                "symbol": "005930",
                                "name": "삼성전자",
                                "marketCountry": "KR",
                                "currency": "KRW",
                                "quantity": "100",
                                "lastPrice": "72000",
                                "averagePurchasePrice": "65000",
                                "profitLoss": {"rate": "0.1077"},
                                "dailyProfitLoss": {"rate": "0.041"},
                            },
                            {
                                "symbol": "AAPL",
                                "name": "Apple Inc.",
                                "marketCountry": "US",
                                "currency": "USD",
                                "quantity": "10",
                                "lastPrice": "178.5",
                                "averagePurchasePrice": "155.3",
                                "profitLoss": {"rate": "0.1494"},
                                "dailyProfitLoss": {"rate": "-0.028"},
                            },
                        ]
                    }
                },
            )

        if url.endswith("/api/v1/candles"):
            return FakeResponse(
                200,
                {
                    "result": {
                        "candles": [
                            {
                                "timestamp": "2026-03-25T09:00:00+09:00",
                                "openPrice": "71600",
                                "highPrice": "72300",
                                "lowPrice": "71500",
                                "closePrice": "72000",
                                "volume": "7521000",
                            },
                            {
                                "timestamp": "2026-03-24T09:00:00+09:00",
                                "openPrice": "71200",
                                "highPrice": "71800",
                                "lowPrice": "71000",
                                "closePrice": "71600",
                                "volume": "2984000",
                            },
                            {
                                "timestamp": "2026-03-23T09:00:00+09:00",
                                "openPrice": "71000",
                                "highPrice": "71400",
                                "lowPrice": "70800",
                                "closePrice": "71200",
                                "volume": "3012000",
                            },
                        ],
                        "nextBefore": None,
                    }
                },
            )

        raise AssertionError(f"unexpected URL {url}")


def make_client():
    config = TossConfig(
        base_url="https://openapi.tossinvest.com",
        client_id="test-client-id",
        client_secret="test-client-secret",
        access_token="",
    )
    session = FakeSession()
    return TossClient(config, session=session), session


def test_get_holdings_end_to_end():
    client, session = make_client()

    holdings = client.get_holdings()

    assert len(holdings) == 2
    kr, us = holdings
    assert kr.ticker == "005930"
    assert kr.name == "삼성전자"
    assert kr.market_country == "KR"
    assert round(kr.change_pct, 2) == 4.1
    assert us.ticker == "AAPL"
    assert round(us.change_pct, 2) == -2.8

    # token requested once, then reused for both accounts + holdings calls
    post_calls = [r for r in session.requests if r[0] == "POST"]
    assert len(post_calls) == 1


def test_get_daily_candles_end_to_end():
    client, _ = make_client()

    candles = client.get_daily_candles("005930", count=3)

    assert len(candles) == 3
    assert candles[0].volume == 7521000
    assert candles[1].volume == 2984000


def test_account_seq_is_cached_across_calls():
    client, session = make_client()

    client.get_holdings()
    client.get_holdings()

    account_calls = [r for r in session.requests if r[1].endswith("/api/v1/accounts")]
    assert len(account_calls) == 1
