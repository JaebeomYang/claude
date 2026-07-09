# 포트폴리오 뉴스 다이제스트 & 알림 모니터

토스증권 Open API에서 보유 종목을 가져와서:

- **`portfolio_monitor.digest_main`** — 2시간마다, 종목별 최근 뉴스를 모아
  다이제스트로 발송합니다 (시세 변동 관련 키워드에 걸리는 헤드라인은 별도 표시).
- **`portfolio_monitor.alert_main`** — 1시간마다, 아래 조건에 해당하면 알림을
  보냅니다:
  - 당일 등락률이 ±3% 이상 (`ALERT_PRICE_CHANGE_PCT`)
  - 거래량이 평균 대비 2배 이상 (`ALERT_VOLUME_MULTIPLE`)
  - 실적, 인수합병, 소송, 신용등급 강등 등 중요 이벤트 키워드가 포함된 뉴스
    헤드라인 발견 (키워드 목록은 `portfolio_monitor/news.py` 참고)

알림은 설정된 채널로 전부 전송됩니다 — 이메일, Slack, Discord 중 설정된
채널 모두에 매번 발송하며 (`portfolio_monitor/notify.py`), 한 채널이
실패해도 나머지 채널은 정상적으로 발송됩니다.

## 설치

```
pip install -r requirements.txt
cp .env.example .env   # 값을 채워넣고, .env 파일 자체는 절대 커밋하지 않는다
```

필요한 환경변수 목록은 `.env.example`에 정리되어 있습니다. 인증 정보는
항상 환경변수로만 읽어오며, 소스 코드에는 절대 하드코딩하지 않습니다.

## 토스증권 Open API 연동

`src/portfolio_monitor/toss_client.py`는 공식 `openapi.tossinvest.com`
OpenAPI 스펙(v1.2.2)을 그대로 따라 구현했습니다:

- `POST /oauth2/token` — `client_credentials` 방식, form-urlencoded로 전송.
  클라이언트당 유효한 액세스 토큰은 1개뿐이며, 재발급 시 이전 토큰은
  즉시 무효화됩니다.
- `GET /api/v1/accounts` — 증권 계좌의 `accountSeq`를 조회하고, 이후
  계좌 관련 API 호출 시 `X-Tossinvest-Account` 헤더로 사용합니다.
- `GET /api/v1/holdings` — 보유 종목(수량, 현재가, 일간/누적 손익률) 조회.
  거래량 정보는 포함하지 않습니다.
- `GET /api/v1/candles?interval=1d` — 일봉 데이터로 당일 거래량과 과거
  평균 거래량을 구해 거래량 급증 알림에 사용합니다 (보유 종목 API 자체엔
  거래량이 없기 때문).

## 실행

```
python -m portfolio_monitor.digest_main
python -m portfolio_monitor.alert_main
```

두 스크립트 모두 스케줄러(Routine/cron 등)가 각자의 주기에 맞춰 호출하는
방식으로 사용하도록 만들어졌습니다.

## 테스트

```
pip install pytest
pytest
```

- `tests/test_alerts.py` — 알림 규칙 로직 (순수 함수, 외부 I/O 없음)
- `tests/test_notify.py` — 다중 채널 발송/실패 시 대체 동작 검증
- `tests/test_toss_client_integration.py` — 인증 → 계좌조회 → 보유종목 →
  캔들 조회까지 전체 흐름을, 실제 API 응답 형태 그대로 만든 가짜 HTTP
  세션으로 검증 (이 환경에서는 실제 API 네트워크 접근이 불가능해서
  대신 사용한 스모크 테스트)
