import logging
from datetime import datetime
from pathlib import Path

import allure
from playwright.sync_api import Page

logger = logging.getLogger(__name__)


class BasePage:
    def __init__(self, page: Page) -> None:
        self.page = page

    @allure.step("Take screenshot: {name}")
    def take_screenshot(self, name: str) -> None:
        # ONLY place page.screenshot() is called in the entire project
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = Path("artifacts") / f"{name}_{timestamp}.png"
        self.page.screenshot(path=str(path))
        with open(path, "rb") as f:
            allure.attach(
                f.read(),
                name=name,
                attachment_type=allure.attachment_type.PNG,
            )
        logger.info("Screenshot saved: %s", path)

    # GAP 5: decorated with @allure.step so every added item appears as a
    # named step in the Allure report alongside its screenshot.
    @allure.step("Log item added: {item_name}")
    def log_item_added(self, item_name: str, url: str) -> None:
        logger.info("Added to cart | item=%s | url=%s", item_name, url)
        allure.attach(
            f"Item: {item_name}\nURL: {url}",
            name=f"cart_add_{item_name}",
            attachment_type=allure.attachment_type.TEXT,
        )

    def wait_for_load(self) -> None:
        self.page.wait_for_load_state("networkidle")
