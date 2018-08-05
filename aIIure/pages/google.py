from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from webium import BasePage, Find, Finds
from webium.driver import get_driver_no_init

class GooglePage(BasePage):
    url = "https://www.google.com"
    search_field = Find(by=By.NAME, value="q")
    search_button = Find(by=By.NAME, value="btnK")
    def open(self):
        BasePage.open(self)
        assert "Google" in get_driver_no_init().title


    def search(self, text_to_search):
        self.search_field.send_keys(text_to_search)
        self.search_field.submit()
        return ResultPage()


class ResultItem(WebElement):
    link = Find(by=By.CSS_SELECTOR, value="h3 a")
    found_words = Finds(by=By.TAG_NAME, value="b")


class ResultPage(BasePage):
    statistics = Find(by=By.ID, value="resultStats")
    results = Finds(ResultItem, By.CLASS_NAME, "rc")