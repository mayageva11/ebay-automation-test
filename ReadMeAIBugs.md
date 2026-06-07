# ReadMeAIBugs 

---

## Bug 1 — Unnecessary and Misleading Import

**Problematic line:**
```python
from selenium import webdriver
```

**Problem:**
The code uses Playwright exclusively, yet imports `selenium`. This is misleading — a reader assumes Selenium is used somewhere. Mixing two browser automation frameworks in the same file is an anti-pattern. If Selenium is not installed in the environment, the entire script crashes at import time before a single line of test code runs.

**Fix:**
```python
# Remove the line entirely — it is unused
from playwright.sync_api import sync_playwright
import time
```

---

## Bug 2 — Resource Leak (Playwright context never closed)

**Problematic line:**
```python
browser = sync_playwright().start().chromium.launch()
```

**Problem:**
`sync_playwright().start()` opens a Playwright managed context that is never closed. `browser.close()` at the end of the function closes the browser process, but the underlying Playwright instance remains open. This causes a memory leak and leaves background processes running after the test finishes.

**Fix:**
```python
def test_search_functionality():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://example.com")
        # ... rest of the code ...
        browser.close()
```

---

## Bug 3 — Hard-coded `time.sleep()` Instead of Smart Waits

**Problematic lines:**
```python
time.sleep(2)
# ...
time.sleep(3)
```

**Problem:**
Hard-coded sleeps are a classic anti-pattern in test automation. If the page loads faster than the sleep duration, the test wastes time. If the page loads slower (server load, slow network), the test fails non-deterministically — a "flaky test". Playwright provides built-in smart waits that only wait as long as necessary.

**Fix:**
```python
# Instead of time.sleep(2) after goto:
page.wait_for_load_state("networkidle")

# Instead of time.sleep(3) after click:
page.wait_for_selector(".result-item")
```

---

## Bug 4 — Overly Generic Locator

**Problematic line:**
```python
page.locator(".button").click()
```

**Problem:**
`.button` is a generic CSS class that may match multiple elements on the page. Playwright will click the **first match** — which is not necessarily the search button. This is a hard-to-diagnose bug because it sometimes works and sometimes doesn't, depending on the order in which elements are rendered on the page.

**Fix:**
```python
page.get_by_role("button", name="Search").click()
# or more specifically:
page.locator("button[type='submit']").click()
```

---

## Bug 5 — No Assertion (the test never actually verifies anything)

**Problematic lines:**
```python
results = page.locator(".result-item")
browser.close()
```

**Problem:**
`results` is stored in a variable but never validated — there is no `assert`, no `expect`, no check that any results appeared at all. The test will **pass** even if the search returned 0 results, the page stayed blank, or the selector is completely wrong. This makes the test worthless as a quality gate.

**Fix:**
```python
results = page.locator(".result-item")
assert results.count() > 0, "No search results found for 'playwright testing'"
browser.close()
```
