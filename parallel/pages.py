import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.select import Select
from webium import BasePage, Find, Finds

logger = logging.getLogger(__name__)
logger.setLevel('INFO')


class APage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)

    @property
    def title(self):
        return self._driver.title

    def close(self):
        self._driver.close()


class MoviePage(APage):
    pass


class FacebookPage(APage):
    pass


class TwitterPage(APage):
    pass


class MovieItem(WebElement):
    poster = Find(by=By.CLASS_NAME, value='posterColumn')
    _title = Find(by=By.CLASS_NAME, value='titleColumn')
    _year = Find(by=By.CLASS_NAME, value='secondaryInfo')
    _imdb_rating = Find(by=By.CLASS_NAME, value='imdbRating')
    your_rating = Find(by=By.CLASS_NAME, value='seen-widget')
    add_to_watchlist = Find(by=By.CLASS_NAME, value='wl-ribbon')

    @property
    def poster_link(self):
        return self.poster.find_element_by_tag_name('a').get_attribute('href')

    @property
    def title(self):
        return self._title.text.split('.')[1].strip()

    @property
    def title_link(self):
        return self._title.find_element_by_tag_name('a').get_attribute('href')

    @property
    def rank(self):
        return int(self._title.text.split('.')[0])

    @property
    def year(self):
        return int(self._year.text[1:-1])

    @property
    def imdb_rating(self):
        return float(self._imdb_rating.text)

    @property
    def number_of_ratings(self):
        voices = self._imdb_rating.find_element_by_tag_name('strong').get_attribute('title').split()[3]
        return int(voices.replace(',', '_'))

    def click(self):
        self._title.find_element_by_tag_name('a').click()
        return MoviePage(self._parent)


class TopRatedPage(APage):
    url = 'https://www.imdb.com/chart/top'
    header = Find(by=By.CSS_SELECTOR, value='h1.header')
    movies = Finds(MovieItem, by=By.CSS_SELECTOR, value='.lister-list tr')
    _sort_by = Find(by=By.CLASS_NAME, value='lister-sort-by')
    _share_button = Find(by=By.CLASS_NAME, value='share-button')
    _share_widget = Find(by=By.ID, value='social-sharing-widget')

    def __init__(self, driver):
        super().__init__(driver)
        self._driver.get(self.url)

    @property
    def title(self):
        return self._driver.title

    def sort_by(self, mode):
        logger.info('Sort by {}'.format(mode))
        if self._driver.capabilities['browserName'] == 'firefox':
            # Select wrapper raises error: 'TypeError: Object of type 'WebElement' is not JSON serializable'
            self._sort_by.click()
            options = self._sort_by.find_elements_by_tag_name('option')
            for option in options:
                if option.text == mode:
                    option.click()
        else:
            Select(self._sort_by).select_by_visible_text(mode)

    def get_sort_mode(self):
        return self._sort_by.find_element_by_css_selector('[selected=selected]').text

    def is_ascending_by(self, field, speedup_step=25):
        _movies = self.movies[::speedup_step]
        return all(getattr(_movies[i], field) <= getattr(_movies[i + 1], field) for i in range(len(_movies) - 1))

    def is_descending_by(self, field, speedup_step=25):
        _movies = self.movies[::speedup_step]
        return all(getattr(_movies[i], field) >= getattr(_movies[i + 1], field) for i in range(len(_movies) - 1))

    @property
    def share_options(self):
        return self._share_widget.find_elements_by_tag_name('a')

    def share_by(self, title):
        self._share_button.click()
        current = self._driver.window_handles
        for option in self.share_options:
            if option.get_attribute('title') == title:
                option.click()
        if 'Facebook' in title:
            new = set(self._driver.window_handles) - set(current)
            self._driver.switch_to.window(new.pop())
            return FacebookPage(self._driver)
        if 'Twitter' in title:
            new = set(self._driver.window_handles) - set(current)
            self._driver.switch_to.window(new.pop())
            return TwitterPage(self._driver)
