# Portfolio news digest & alert monitor

Pulls current holdings from the Toss Invest Open API and:

- **`portfolio_monitor.digest_main`** — every 2 hours, emails a news digest
  for each holding (recent headlines, flags anything matching a list of
  market-moving keywords).
- **`portfolio_monitor.alert_main`** — hourly, emails an alert when a holding:
  - moves ±3% or more in a day (`ALERT_PRICE_CHANGE_PCT`)
  - trades at 2x+ its average volume (`ALERT_VOLUME_MULTIPLE`)
  - has a news headline matching an important-event keyword (earnings,
    merger, lawsuit, downgrade, etc. — see `portfolio_monitor/news.py`)

## Setup

```
pip install -r requirements.txt
cp .env.example .env   # fill in credentials, do not commit .env
```

Required env vars are documented in `.env.example`. Credentials are only
ever read from the environment — nothing is hardcoded in the source.

## Toss Invest Open API integration

`src/portfolio_monitor/toss_client.py` is implemented against the official
`openapi.tossinvest.com` OpenAPI spec (v1.2.2):

- `POST /oauth2/token` — `client_credentials` grant, form-urlencoded. One
  valid access token per client; reissuing invalidates the previous one.
- `GET /api/v1/accounts` — resolves the brokerage account's `accountSeq`,
  used as the `X-Tossinvest-Account` header on every account-scoped call.
- `GET /api/v1/holdings` — current holdings (quantity, prices, daily/total
  P&L rates). Does not report volume.
- `GET /api/v1/candles?interval=1d` — daily OHLCV, used to get today's
  volume and a trailing average for the volume-spike alert (holdings
  themselves don't include volume).

## Running

```
python -m portfolio_monitor.digest_main
python -m portfolio_monitor.alert_main
```

These are meant to be invoked on a schedule (e.g. a Routine/cron calling
each command on its respective cadence).

## Tests

```
pip install pytest
pytest
```

Covers the alert-rule logic (`tests/test_alerts.py`), which is pure and
doesn't require live API/network access.
