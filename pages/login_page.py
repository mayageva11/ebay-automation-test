import allure
from playwright.sync_api import Page

from pages.base_page import BasePage


class LoginPage(BasePage):
    USERNAME_INPUT      = "input[name='email']"
    PASSWORD_INPUT      = "input[name='password']"
    SUBMIT_BUTTON       = "input[value='Login']"
    LOGIN_ERROR = ".alert-danger, .alert-warning"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    @allure.step("Login to the application")
    def login(self, credentials: dict, login_url: str) -> None:
        # login_url is a method parameter — not a constructor arg.
        # Keeps __init__(self, page) consistent with all other Page Objects.
        self.page.goto(login_url)
        self.wait_for_load()

        # If the session is already authenticated the site redirects away from
        # the login page immediately — no form to fill in that case.
        if "route=account/login" not in self.page.url:
            self.take_screenshot("login_success")
            return

        self.page.wait_for_selector(self.USERNAME_INPUT)
        self.page.fill(self.USERNAME_INPUT, credentials["username"])

        self.page.wait_for_selector(self.PASSWORD_INPUT)
        self.page.fill(self.PASSWORD_INPUT, credentials["password"])

        self.page.wait_for_selector(self.SUBMIT_BUTTON, state="visible")
        self.page.click(self.SUBMIT_BUTTON)
        self.wait_for_load()

        # Fail immediately with the site's own error message if login was rejected
        error_el = self.page.query_selector(self.LOGIN_ERROR)
        if error_el:
            self.take_screenshot("login_failed")
            raise RuntimeError(f"Login failed: {error_el.inner_text().strip()}")

        # If still on the login page after submit, something else went wrong
        if "route=account/login" in self.page.url:
            self.take_screenshot("login_failed")
            raise RuntimeError("Login failed: form submitted but page did not redirect")

        self.take_screenshot("login_success")
