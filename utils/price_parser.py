import re


class PriceParser:
    # Matches optional "US " prefix then a dollar amount: $1,220.00 or $50
    _PATTERN = re.compile(r'(?:US\s*)?\$[\d,]+(?:\.\d+)?')

    @staticmethod
    def parse(price_str: str) -> float | None:
        """
        Extracts the first dollar amount from a price string.

        Examples:
            "$220.00"              → 220.0
            "$1,220.00"            → 1220.0
            "From $50"             → 50.0   (first match only)
            "US $180.00"           → 180.0
            "$180 + $12 shipping"  → 180.0  (first match, ignores shipping)
            "Best offer"           → None   (no dollar sign)
        """
        match = PriceParser._PATTERN.search(price_str)
        if not match:
            return None
        raw = match.group()
        # Strip "US ", "$", and "," then cast to float
        clean = raw.replace("US ", "").replace("$", "").replace(",", "")
        return float(clean)


# ---------------------------------------------------------------------------
# Unit tests — run with: pytest utils/price_parser.py -v
# ---------------------------------------------------------------------------

class TestPriceParser:
    def test_plain_decimal(self):
        assert PriceParser.parse("$220.00") == 220.0

    def test_thousands_separator(self):
        assert PriceParser.parse("$1,220.00") == 1220.0

    def test_from_prefix(self):
        assert PriceParser.parse("From $50") == 50.0

    def test_us_prefix(self):
        assert PriceParser.parse("US $180.00") == 180.0

    def test_plus_shipping(self):
        assert PriceParser.parse("$180 + $12 shipping") == 180.0

    def test_best_offer_returns_none(self):
        assert PriceParser.parse("Best offer") is None

    def test_empty_string_returns_none(self):
        assert PriceParser.parse("") is None

    def test_integer_price(self):
        assert PriceParser.parse("$50") == 50.0
