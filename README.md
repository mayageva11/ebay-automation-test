# eBay-like E2E Automation Framework

End-to-end test automation for [ecommerce-playground.lambdatest.io](https://ecommerce-playground.lambdatest.io) using Python, Playwright, and Allure.

## Stack

- Python 3.11+
- Playwright 1.45 (Chromium)
- pytest 8.2 with parametrize
- Allure Reports + Playwright Trace

## Quick start

```bash
make install   # install Python packages + Chromium (once)
make test      # run the tests — a browser window opens so you can watch
make report    # open the Allure HTML report
```

That's it. All commands are in the `Makefile`.

---

## Before running — set your credentials

Copy the example file and fill in your details:

```bash
cp test_data.json.example test_data.json
```

Then open `test_data.json` and replace the credentials with a registered account on `ecommerce-playground.lambdatest.io`:

```json
"credentials": {
  "username": "your_email@example.com",
  "password": "YourPassword"
}
```

Register a free account at:
`https://ecommerce-playground.lambdatest.io/index.php?route=account/register`

> **Note:** `test_data.json` is git-ignored. Never commit real credentials.

## All available commands

| Command | What it does |
|---|---|
| `make install` | Install dependencies + Chromium browser |
| `make test` | Run all E2E tests (browser visible) |
| `make test-headless` | Run without a browser window (for CI) |
| `make report` | Open Allure HTML report |
| `make clean` | Delete screenshots, reports, cache |

The report includes:
- Feature / Story tags
- Per-step screenshots attached inline
- Text log of every item added to cart
- Environment panel (URL, browser, Python version)
- Playwright Trace attachment

## View Playwright Trace

After a run, open the trace in the browser-based viewer:

1. Go to [trace.playwright.dev](https://trace.playwright.dev)
2. Drop `artifacts/trace.zip` onto the page

The trace shows every action, network request, and DOM snapshot for the full session.

## Test Report

Run the tests and open the report with:

```bash
make test
make report
```

The Allure dashboard shows:
- Full test list with pass/fail status per parametrized scenario
- Every step expanded with its screenshot attached inline
- Text log of each item added to cart
- Environment panel (URL, browser, Python version)
- Downloadable Playwright Trace (drop `artifacts/trace.zip` on
  https://trace.playwright.dev to replay the full session)

> ![Allure Report](docs/allure_report_screenshot.png)

## Limitations & Assumptions

- **Real login required** — the site does not support guest checkout. A registered account on `ecommerce-playground.lambdatest.io` is mandatory. Registration is free.
- **Email verification** — the site requires email verification after registration. Unverified accounts cannot add items to cart.
- **Currency** — all prices are parsed and compared in USD as displayed on the site. No currency conversion is performed.
- **Stock availability** — if all items returned by a search are out of stock or have no valid variant options, the test is skipped with a clear error message. This is expected behaviour, not a bug.
- **Budget threshold** — `assertCartTotalNotExceeds` uses the number of items actually added to the cart (not the number of URLs found). Items that failed due to stock or missing variants do not inflate the threshold, making the assertion stricter and more meaningful.
- **Site stability** — `ecommerce-playground.lambdatest.io` is a shared demo environment. Occasional downtime or slow responses may cause flaky runs unrelated to the framework.
- **Viewport** — tests run at 1440×900 to ensure the Bootstrap `lg` breakpoint is active and all buttons are visible.

## Project structure

```
├── conftest.py              # session fixtures (browser, data, tracing)
├── test_data.json           # all test inputs — edit credentials here
├── tests/
│   └── test_ebay_e2e.py     # single parametrized E2E test
├── pages/
│   ├── base_page.py         # BasePage: screenshot, logging, wait_for_load
│   ├── login_page.py
│   ├── search_page.py
│   ├── item_page.py
│   └── cart_page.py
├── models/
│   └── test_data_model.py   # pydantic schema + load_and_validate()
├── utils/
│   └── price_parser.py      # price string → float + unit tests
├── artifacts/               # screenshots + trace.zip (git-ignored)
└── allure-results/          # allure output (git-ignored)
```
