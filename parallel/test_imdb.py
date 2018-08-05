#!/usr/bin/env python3
import os
import logging
import requests
import pytest
from pytest import fixture
from selenium.webdriver import Firefox, Chrome
from pages import TopRatedPage
from webium.wait import wait

logger = logging.getLogger(__name__)
logger.setLevel('INFO')


@fixture(params=[(Firefox, 'geckodriver'), (Chrome, 'chromedriver')],
         ids=['Firefox', 'Chrome'])
def top_250_page(request):
    driver_path = os.path.join(os.getcwd(), 'resources', request.param[1])
    driver = request.param[0](executable_path=driver_path)
    yield TopRatedPage(driver)
    try:
        if request.node.report_call.failed:
            driver.save_screenshot(request.node.screenshot)
    finally:
        driver.quit()


def test_open_page(top_250_page):
    logger.info('Test Top 250 Page')
    assert top_250_page.title == 'IMDb Top 250 - IMDb'
    assert top_250_page.header.text == 'Top Rated Movies'
    assert len(top_250_page.movies) == 250

    logger.info('Check movie item format')
    movie = top_250_page.movies[0]
    assert movie.rank
    assert movie.title
    assert movie.year
    assert movie.imdb_rating
    assert movie.number_of_ratings

    logger.info('Check default sorting by rank')
    assert top_250_page.is_ascending_by('rank')

    logger.info('Check that all posters are displayed')
    assert all(movie.poster.is_displayed() for movie in top_250_page.movies)


def get_http_statuses(url_list, num_of_threads=10):
    from multiprocessing.pool import ThreadPool
    pool = ThreadPool(num_of_threads)
    get_status = lambda x: requests.get(x).status_code
    results = pool.map(get_status, url_list)
    logger.debug(results)
    pool.close()
    pool.join()
    return results


@pytest.mark.skip(reason='It is about minute even in thread pool')
def test_all_links(top_250_page):
    top_250_page._driver.implicitly_wait(60)
    logger.info('Check that all movies can be opened')
    poster_links = [movie.poster_link for movie in top_250_page.movies]
    title_links = [movie.title_link for movie in top_250_page.movies]
    assert poster_links == title_links
    assert all(status == 200 for status in get_http_statuses(title_links))


def test_title_link(top_250_page):
    logger.info('Check that movie page is available by title')
    movie = top_250_page.movies[0]
    expected_title = movie.title
    movie_page = movie.click()
    assert expected_title in movie_page.title


def test_poster_link(top_250_page):
    logger.info('Check that movie page is available by poster')
    movie = top_250_page.movies[0]
    expected_title = movie.title
    movie.poster.click()
    assert expected_title in top_250_page.title


def test_sorting(top_250_page):
    logger.info('Test sorting')
    top_250_page.sort_by('Release Date')
    assert wait(lambda: top_250_page.is_descending_by('year'))

    top_250_page.sort_by('IMDb Rating')
    assert wait(lambda: top_250_page.is_descending_by('imdb_rating'))

    top_250_page.sort_by('Number of Ratings')
    assert wait(lambda: top_250_page.is_descending_by('number_of_ratings'))

    top_250_page.sort_by('Your Rating')
    assert wait(lambda: top_250_page.is_ascending_by('rank'))

    top_250_page.sort_by('Ranking')
    assert wait(lambda: top_250_page.is_ascending_by('rank'))


@pytest.mark.parametrize('sharing, link, title', [
    ('Share on Facebook', 'http://www.facebook.com/sharer.php?u=https%3A%2F%2Fwww.imdb.com%2Fchart%2Ftop', 'Facebook'),
    ('Share on Twitter', 'http://twitter.com/intent/tweet?text=IMDb%20Top%20250%20-%20IMDb%20-%20https%3A%2F%2Fwww.imdb.com%2Fchart%2Ftop', 'Post a Tweet on Twitter'),
    ('Share by Email', 'mailto:?subject=Check%20out%20this%20link%20on%20IMDb!&body=IMDb%20Top%20250%20-%20IMDb%20-%20https://www.imdb.com/chart/top', ''),
    ('Click to Copy', 'https://www.imdb.com/chart/top', ''),
], ids=['Facebook', 'Twitter', 'Email', 'Copy'])
def test_share(top_250_page, sharing, link, title):
    logger.info("Test sharing by {}".format(sharing))
    assert any(link == option.get_attribute('href') for option in top_250_page.share_options)
    page = top_250_page.share_by(sharing)
    if title:
        assert wait(lambda: page.title == title)


if __name__ == '__main__':
    pytest.main(['-vvv', '-s', '--html=result.html', '--self-contained-html', '-log_cli=true', '-n2'])
