import allure
from playwright.sync_api import Page

from pages.base_page import BasePage
from utils.price_parser import PriceParser


class CartPage(BasePage):
    # Cart page uses a plain table; td strong holds the price values.
    # No tfoot, no .table class — actual lambdatest cart HTML structure.
    SUBTOTAL_ROW = "td strong"
    TOTAL_ROW    = "tr:last-child td strong"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    @allure.step("Clear cart")
    def clear_cart(self, cart_url: str) -> None:
        self.page.goto(cart_url)
        self.wait_for_load()
        # Extract cart item keys from onclick="cart.remove('key')" attributes.
        keys = self.page.evaluate(
            "[...document.querySelectorAll('button[onclick*=\"cart.remove\"]')]"
            ".map(b => {"
            "  const m = (b.getAttribute('onclick')||'').match(/cart\\.remove\\('([^']+)'\\)/);"
            "  return m ? m[1] : null;"
            "}).filter(k => k)"
        )
        if not keys:
            return
        # Remove each item via a background fetch so the page does not navigate
        # or reload — cart.remove() calls window.location which would abort any
        # subsequent page.goto() call.
        for key in keys:
            self.page.evaluate(
                f"fetch('/index.php?route=checkout/cart/remove', {{"
                f"  method: 'POST',"
                f"  headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},"
                f"  body: 'key={key}'"
                f"}})"
            )
        # Wait for all fetch requests to complete before leaving this page.
        self.page.wait_for_load_state("networkidle")

    @allure.step("Read cart total")
    def get_total(self, cart_url: str) -> float:
        self.page.goto(cart_url)
        self.wait_for_load()

        # Screenshot of the full cart page so the report shows all items added
        self.take_screenshot("cart_with_items")

        for selector in [self.TOTAL_ROW, self.SUBTOTAL_ROW]:
            el = self.page.query_selector(selector)
            if el:
                value = PriceParser.parse(el.inner_text())
                if value is not None:
                    self.take_screenshot("cart_total_closeup")
                    return value

        # Cart empty or selector changed — raise explicitly, never silently return 0
        raise ValueError(
            "Could not read cart total: cart may be empty or the selector has changed"
        )

    # GAP 3: assignment signature assertCartTotalNotExceeds(budgetPerItem, itemsCount)
    @allure.step("Assert cart total does not exceed budget")
    def assert_cart_total_not_exceeds(
        self, cart_url: str, budget_per_item: float, items_count: int
    ) -> None:
        total = self.get_total(cart_url)
        threshold = budget_per_item * items_count
        assert total <= threshold, (
            f"Cart total ${total:.2f} exceeds budget "
            f"${threshold:.2f} ({items_count} items × ${budget_per_item:.2f})"
        )
