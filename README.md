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

## Known gap: Toss Open API endpoints are unverified

`src/portfolio_monitor/toss_client.py` implements a `client_credentials`
OAuth2 flow against `POST {base_url}/oauth2/token` and reads holdings from
`GET {base_url}/v1/accounts/holdings`. These paths and the response shape
are best-effort guesses — outbound network access to
`developers.tossinvest.com` was blocked in the environment this was
written in, so the real API docs could not be checked. Before running this
against a live account:

1. Confirm the token endpoint, grant type, and holdings endpoint/response
   shape against the official docs.
2. Update `TossClient._ensure_token` / `TossClient.get_holdings` in
   `toss_client.py` accordingly (the public interface — `get_holdings()`
   returning a list of `Holding` — is stable, so callers won't need to
   change).

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
