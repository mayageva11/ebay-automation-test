import allure
from playwright.sync_api import Page

from pages.base_page import BasePage
from utils.price_parser import PriceParser


class SearchPage(BasePage):
    SEARCH_INPUT     = "input[name='search']"
    SEARCH_BUTTON    = "button.type-submit"
    ITEM_LINK        = "//div[contains(@class,'product-thumb')]//h4/a"           # XPath — required by assignment
    ITEM_PRICE       = "//div[contains(@class,'product-thumb')]//*[contains(@class,'price')]"  # XPath — required by assignment
    PRICE_MIN_INPUT  = "input#input-min"   # GAP 2: fill with "0" alongside max filter
    PRICE_MAX_INPUT  = "input#input-max"
    APPLY_FILTER_BTN = "button#button-search"
    NEXT_PAGE        = "ul.pagination li a[aria-label='Next']"

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page)
        self._base_url = base_url.rstrip("/")

    def _collect_page_items(self, max_price: float) -> list[str]:
        links  = self.page.query_selector_all(f"xpath={self.ITEM_LINK}")
        prices = self.page.query_selector_all(f"xpath={self.ITEM_PRICE}")
        results = []
        for link, price_el in zip(links, prices):
            for attempt in range(3):
                try:
                    price_text = price_el.inner_text()
                    href = link.get_attribute("href")
                    break
                except Exception:
                    if attempt == 2:
                        raise
                    self.page.wait_for_timeout(500)
            price = PriceParser.parse(price_text)
            if price is None or price > max_price:
                continue
            if href:
                results.append(href)
        return results

    def _paginate(self, max_price: float, limit: int, results: list[str]) -> list[str]:
        # while loop — NOT recursive: avoids stack overflow and result loss on exceptions
        while len(results) < limit:
            if not self.page.is_visible(self.NEXT_PAGE):
                break  # no more pages — 0 results is valid
            next_href = self.page.get_attribute(self.NEXT_PAGE, "href")
            self.page.goto(next_href)
            self.wait_for_load()
            results.extend(self._collect_page_items(max_price))
        return results[:limit]

    @allure.step("Search '{query}' under ${max_price}, limit {limit}")
    def search_items_by_name_under_price(
        self, query: str, max_price: float, limit: int
    ) -> tuple[list[str], str]:
        self.page.goto(
            f"{self._base_url}/index.php?route=product/search&search={query}"
        )
        self.wait_for_load()

        # Apply min/max price filter if the controls exist on the page.
        # GAP 2: both PRICE_MIN_INPUT and PRICE_MAX_INPUT are filled when available.
        # Code-side price check in _collect_page_items always runs regardless.
        if self.page.is_visible(self.PRICE_MAX_INPUT):
            if self.page.is_visible(self.PRICE_MIN_INPUT):
                self.page.fill(self.PRICE_MIN_INPUT, "0")
            self.page.fill(self.PRICE_MAX_INPUT, str(max_price))
            self.page.wait_for_selector(self.APPLY_FILTER_BTN, state="visible")
            self.page.click(self.APPLY_FILTER_BTN)
            self.wait_for_load()

        # Saved AFTER filters applied, BEFORE any item navigation.
        # Avoids dynamic session-token drift that breaks goto(search_url) on later items.
        search_url = self.page.url

        results = self._collect_page_items(max_price)
        if len(results) < limit:
            results = self._paginate(max_price, limit, results)

        self.take_screenshot(f"search_results_{query}")
        return results[:limit], search_url
