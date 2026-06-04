import logging
import random
import re

import allure
from playwright.sync_api import Page

from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class ItemPage(BasePage):
    # Selectors verified against ecommerce-playground.lambdatest.io product pages
    ITEM_TITLE     = "h1"
    SUCCESS_BANNER = ".alert-success, #cart-total"   # checked after add
    OPTION_SELECTS = "select[name^='option']"        # OpenCart variant dropdowns
    QTY_INPUT      = "input[name='quantity']"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    # GAP 4: assignment signature addItemsToCart(urls) as a named method
    @allure.step("Add {urls} items to cart")
    def add_items_to_cart(self, urls: list[str], search_url: str) -> list[int]:
        """Returns list of quantities actually added (0-entries excluded)."""
        quantities = []
        for url in urls:
            qty = self.add_to_cart_from_url(url, search_url)
            if qty > 0:
                quantities.append(qty)
        return quantities

    @allure.step("Add to cart: {url}")
    def add_to_cart_from_url(self, url: str, search_url: str) -> int:
        self.page.goto(url)
        self.wait_for_load()

        # Extract product_id from the URL so we can call cart.add(pid) directly.
        # Clicking the "Add to Cart" button does not work on this site because its
        # JavaScript event listener attaches asynchronously after page load, so the
        # click fires before the handler is registered. cart.add() is the same code
        # path used by the listing page quick-add buttons and is always available.
        pid_match = re.search(r'product_id=(\d+)', url)
        if not pid_match:
            self.page.goto(search_url)
            return 0
        pid = pid_match.group(1)

        # Screenshot of the product page before interacting
        item_name = self.page.locator(self.ITEM_TITLE).first.inner_text()
        self.take_screenshot(f"product_page_{item_name}")

        # Select a random valid value for every required option dropdown.
        # If an option has no valid values (broken product data), skip this item.
        selects = self.page.query_selector_all(self.OPTION_SELECTS)
        for sel_el in selects:
            sel_name = sel_el.get_attribute("name") or ""
            opts = self.page.evaluate(
                f"[...document.querySelectorAll(\"select[name='{sel_name}'] option\")]"
                f".map(o => ({{value: o.value, disabled: o.disabled}}))"
            )
            valid = [o["value"] for o in opts if o["value"] and not o["disabled"]]
            if not valid:
                self._log_skip(url, f"option '{sel_name}' has no available values")
                self.page.goto(search_url)
                return 0
            self.page.select_option(f"select[name='{sel_name}']", random.choice(valid))

        # Randomize quantity 1–3; returned so the test can calculate the real threshold.
        qty = random.randint(1, 3)
        if self.page.is_visible(self.QTY_INPUT):
            self.page.fill(self.QTY_INPUT, str(qty))

        # Screenshot showing variant selections and quantity before clicking Add to Cart
        self.take_screenshot(f"before_add_to_cart_{item_name}")

        # Add to cart via JavaScript — equivalent to the listing page quick-add.
        added = self._js_add_to_cart(pid, qty)
        if not added:
            self.page.goto(search_url)
            return 0

        # GAP 5: take_screenshot is called after successful add,
        # then log_item_added (decorated with @allure.step) records it as a named step.
        self.take_screenshot(f"added_to_cart_{item_name}")
        self.log_item_added(item_name, url)

        self.page.goto(search_url)   # never go_back()
        return qty

    def _js_add_to_cart(self, pid: str, qty: int) -> bool:
        """
        Calls cart.add(pid, qty) via JavaScript and reads the server response.
        Uses expect_response() — the correct Playwright pattern for capturing
        the response from an action that triggers an AJAX request.
        Returns True on success, False on server error or timeout.
        """
        for attempt in range(3):
            try:
                with self.page.expect_response(
                    lambda r: "checkout/cart/add" in r.url,
                    timeout=8000,
                ) as resp_info:
                    self.page.evaluate(f"cart.add('{pid}', '{qty}')")
                body = resp_info.value.text()
                if '"success"' in body:
                    return True
                logger.warning("cart.add(%s) rejected by server: %s", pid, body[:200])
                return False
            except Exception as exc:
                if attempt == 2:
                    logger.warning("cart.add(%s) no response after 3 attempts: %s", pid, exc)
                    return False
                self.page.wait_for_timeout(500)

    def _log_skip(self, url: str, reason: str) -> None:
        logger.warning("Skipped %s — %s", url, reason)
        pid = url.split("product_id=")[-1].split("&")[0]
        self.take_screenshot(f"skipped_{pid}")
