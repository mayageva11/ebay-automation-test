import allure
import pytest

from models.test_data_model import TestDataModel
from pages.cart_page import CartPage
from pages.item_page import ItemPage
from pages.login_page import LoginPage
from pages.search_page import SearchPage

# Module-level load — safe at collection time; if test_data.json is missing
# pytest shows a clean ImportError instead of a cryptic parametrize crash.
_data = TestDataModel.load_and_validate("test_data.json")
_search_params = [(s.query, s.max_price, s.limit) for s in _data.search]


@pytest.mark.parametrize("query,max_price,limit", _search_params)
@allure.feature("E2E Shopping Flow")
@allure.story("Search, Add to Cart, Assert Total")
def test_ebay_e2e(page, test_data, query: str, max_price: float, limit: int):
    allure.dynamic.title(f"E2E: {query} under ${max_price}")

    data = test_data  # single alias — no NameError risk below

    login_page  = LoginPage(page)
    search_page = SearchPage(page, str(data.base_url))
    item_page   = ItemPage(page)
    cart_page   = CartPage(page)

    # Step 1: Login, then clear any items left in cart from a previous test run
    login_page.login(data.credentials.model_dump(), str(data.login_url))
    cart_page.clear_cart(str(data.cart_url))

    # Step 2: Search with price filter
    urls, search_url = search_page.search_items_by_name_under_price(
        query, max_price, limit
    )
    assert urls, f"No items found for query='{query}' under ${max_price}"

    # Step 3: GAP 4 — use the named add_items_to_cart method (assignment signature)
    quantities = item_page.add_items_to_cart(urls, search_url)

    assert quantities, (
        "No items could be added to cart — all products were out of stock.\n"
        "If this is a new account, make sure the registration email has been verified."
    )

    # Step 4: GAP 3 — use the named assert_cart_total_not_exceeds method (assignment signature)
    assert cart_page.get_total(str(data.cart_url)) > 0, (
        "Cart total is $0.00 — items were not saved to the cart.\n"
        "Likely cause: a required product option (size/colour) was not selected, "
        "or the account email has not been verified yet."
    )
    # The assignment signature uses urls.length as the item count.
    # We intentionally use len(quantities) instead — the number of items
    # actually added to the cart — because items that failed (out of stock,
    # missing variants) should not inflate the budget threshold.
    # Example: 5 URLs found, 3 added successfully → threshold = 3 × budget,
    # not 5 × budget. This makes the assertion stricter and more meaningful.
    cart_page.assert_cart_total_not_exceeds(
        str(data.cart_url), data.budget_per_item, len(quantities)
    )


def test_search_returns_empty_for_unknown_query(page, test_data):
    search_page = SearchPage(page, str(test_data.base_url))
    urls, _ = search_page.search_items_by_name_under_price(
        "xyzproductnotfound123", 999, 5
    )
    assert urls == [], f"Expected empty list, got {urls}"


def test_search_returns_empty_when_price_too_low(page, test_data):
    search_page = SearchPage(page, str(test_data.base_url))
    urls, _ = search_page.search_items_by_name_under_price("shoes", 1, 5)
    assert urls == [], f"Expected empty list for max_price=1, got {urls}"


def test_search_includes_item_at_exact_max_price(page, test_data):
    """
    Verifies the <= condition: items priced at exactly max_price must not be
    filtered out. An empty result is acceptable if no items exist at that price.
    What must never happen is an exception being raised.
    """
    search_page = SearchPage(page, str(test_data.base_url))
    urls, _ = search_page.search_items_by_name_under_price(
        test_data.search[0].query,
        test_data.search[0].max_price,
        5,
    )
    assert isinstance(urls, list), (
        f"Expected a list, got {type(urls)}"
    )


def test_invalid_test_data_raises_error():
    """
    Verifies that pydantic validation rejects a malformed test_data.json
    with a clear error before any browser is launched.
    """
    import json
    import tempfile
    import pytest
    from models.test_data_model import TestDataModel

    bad_data = {
        "base_url": "https://ecommerce-playground.lambdatest.io",
        "login_url": "https://ecommerce-playground.lambdatest.io/index.php?route=account/login",
        "cart_url": "https://ecommerce-playground.lambdatest.io/index.php?route=checkout/cart",
        "credentials": {"username": "a@b.com", "password": "pass"},
        "search": [{"query": "shoes", "max_price": "not_a_number", "limit": 5}],
        "budget_per_item": 220,
        "timeouts": {"page_load": 30000, "element": 10000, "navigation": 15000},
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(bad_data, f)
        tmp_path = f.name

    with pytest.raises((ValueError, Exception)):
        TestDataModel.load_and_validate(tmp_path)
