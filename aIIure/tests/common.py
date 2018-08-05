from webium.driver import close_driver


class BaseTest(object):
    def teardown_class(self):
        close_driver()