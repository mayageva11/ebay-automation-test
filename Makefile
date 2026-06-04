# ─────────────────────────────────────────────────────────────
#  eBay-like E2E Automation — task runner
#  Usage:  make <target>
# ─────────────────────────────────────────────────────────────

.PHONY: install test test-headless report clean help

# Install all Python dependencies and the Chromium browser
install:
	pip3 install -r requirements.txt
	playwright install chromium

# Run the full E2E test suite (browser window opens so you can watch)
test:
	pytest tests/ --alluredir=allure-results -v

# Same run but without a visible browser window (CI-friendly)
test-headless:
	HEADLESS=true pytest tests/ --alluredir=allure-results -v

# Open the Allure HTML report after a test run
report:
	allure serve allure-results

# Remove all generated files so you can start fresh
clean:
	rm -rf artifacts/ allure-results/ .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Print this help
help:
	@echo ""
	@echo "  make install       Install dependencies + Chromium"
	@echo "  make test          Run E2E tests (visible browser)"
	@echo "  make test-headless Run E2E tests (no browser window)"
	@echo "  make report        Open Allure HTML report"
	@echo "  make clean         Delete artifacts and cache"
	@echo ""
