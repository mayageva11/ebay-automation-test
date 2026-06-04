import logging
import sys
from pathlib import Path

import allure
import pytest
from playwright.sync_api import sync_playwright

from models.test_data_model import TestDataModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)


@pytest.fixture(scope="session")
def test_data() -> TestDataModel:
    # Very first fixture — pydantic validation runs before any browser launches.
    # Bad config fails immediately with a clear message.
    return TestDataModel.load_and_validate("test_data.json")


@pytest.fixture(scope="session", autouse=True)
def artifacts_dir():
    Path("artifacts").mkdir(exist_ok=True)


@pytest.fixture(scope="session", autouse=True)
def allure_environment(test_data):
    # Directory must exist before yield — allure-pytest writes result files
    # from the very first test, not at teardown.
    Path("allure-results").mkdir(exist_ok=True)
    yield
    Path("allure-results/environment.properties").write_text(
        f"base_url={test_data.base_url}\n"
        f"browser=chromium\n"
        f"python_version={sys.version.split()[0]}\n",
        encoding="utf-8",
    )


@pytest.fixture(scope="session")
def browser_context(test_data):
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=False)
    # 1440×900 ensures Bootstrap lg breakpoint is active so Add to Cart buttons are visible.
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    # Trace captures screenshots, DOM snapshots, and source for every action
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    yield context
    Path("artifacts").mkdir(exist_ok=True)
    context.tracing.stop(path="artifacts/trace.zip")
    allure.attach.file(
        "artifacts/trace.zip",
        name="playwright_trace",
        attachment_type=allure.attachment_type.ZIP,
    )
    context.close()
    browser.close()
    pw.stop()


@pytest.fixture
def page(browser_context, test_data):
    p = browser_context.new_page()
    p.set_default_timeout(test_data.timeouts.element)
    yield p
    p.close()
