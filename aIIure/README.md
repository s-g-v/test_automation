Example of Web-UI test framework, based on pytest, webium, selenium and allure report framework.
Usage:
pytest -vvv --alluredir=./results ./tests/

Requirements:
1. geckodriver - https://github.com/mozilla/geckodriver/releases - executable should be in PATH
2. allure2 - https://github.com/allure-framework/allure2 - server to make reports. Download, extract and set path
to allure executable to PATH environment variable
Usage: allure serve <path_to_reports>
