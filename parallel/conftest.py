from datetime import datetime

import os
import pytest
from py.xml import html


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, 'report_' + report.when, report)
    screenshot_path = os.path.join(os.getcwd(), item.name + ".png")
    setattr(item, 'screenshot', screenshot_path)
    setattr(report, 'screenshot', screenshot_path)


@pytest.mark.optionalhook
def pytest_html_results_table_header(cells):
    cells.insert(0, html.th('Time', class_='sortable time', col='time'))
    cells.pop()


@pytest.mark.optionalhook
def pytest_html_results_table_row(report, cells):
    cells.insert(0, html.td(datetime.utcnow(), class_='col-time'))
    cells.pop()


@pytest.mark.optionalhook
def pytest_html_results_table_html(report, data):
    if report.outcome == 'failed':
        data[0].append(html.br())
        data[0].append(html.img(src=report.screenshot))
