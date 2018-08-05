#!/usr/bin/env python2
# coding=utf-8
import os
import time
import pytest
import psutil
import requests
import logging
logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)
logging.disable(logging.DEBUG)
log = logging.getLogger(__file__)


QTS_PROCESS = 'qts'
WFE_URL = 'http://localhost:12345/processes'
MM_URL = 'http://localhost:12345/entities/program/{}'


def wait(timeout=10, interval=1):
    """
    Useful wait decorator.
    Usage with function declaration: @wait(60, 1)
    Usage in test code: wait(60)(func_to_wait)(func_params)
    Return: last or successful func_to_wait(func_params) result
    """
    def what(func):
        def whit_args(*args):
            end_time = time.time() + timeout
            result = func(*args)
            while not result and time.time() < end_time:
                time.sleep(interval)
                result = func(*args)
            return result
        return whit_args
    return what


@wait(180)
def check_wfe_status(process, expected_status):
    """Return True if process has expected status in Workflow Engine API"""
    status = [proc['status'] for proc in requests.get(WFE_URL).json() if proc['name'] == process]
    # Assume that process name is unique
    return status and status[0] == expected_status


@pytest.fixture(autouse=True)
def run_qts_mock():
    # Imports are here, because this function is needed only to simulate work of QTS.
    # If set autouse=False and delete mock, then these imports won't affect test case.
    from qts_mock import ApiMock, consume_xml
    from BaseHTTPServer import HTTPServer
    from threading import Thread
    qts = Thread(target=consume_xml)
    qts.daemon = True
    qts.start()
    serv = HTTPServer(("localhost", 12345), ApiMock)
    wfe = Thread(target=serv.serve_forever)
    wfe.start()
    yield
    serv.shutdown()


def test_qts():
    log.info("TestCase: Positive QTS system test")
    dir_name, xml_name, program = 'qts_watch_folder', 'test.xml', 'program_name'

    log.info("Step: Put xml file {} into directory {}".format(xml_name, dir_name))
    template = '<program><name>{}</name></program>'.format(program)
    with open(os.path.join(dir_name, xml_name), 'wt') as f:
        f.write(template)

    log.info("Step: Verify that QTS process is running and file is consumed")
    assert [p.cmdline() for p in psutil.process_iter() if QTS_PROCESS in str(p.cmdline())],\
        'Expected process {} is not running'.format(QTS_PROCESS)
    assert wait(60)(lambda: xml_name not in os.listdir(dir_name))(),\
        'File was not consumed within 60 sec'

    log.info("Step: Verify Workflow Engine process status")
    wfe_processes = requests.get(WFE_URL)
    assert wfe_processes.status_code == 200,\
        'WFE returned error code {}'.format(wfe_processes.status_code)
    assert 'application/json' in wfe_processes.headers['content-type'],\
        'WFE returned unexpected content'
    assert check_wfe_status(program, 'running'), 'Process {} was not running'.format(program)
    # If we need warnings about long processing, then it is possible to use chain of check_wfe_status,
    # but decorator should be changed @wait(60).
    # if not check_wfe_status(program, 'completed'):
    #     log.warn('Process {} was not finished within 60 sec'.format(program))
    # if not check_wfe_status(program, 'completed'):
    #     log.warn('Process {} was not finished even in 120 sec'.format(program))
    assert check_wfe_status(program, 'completed'),\
        'Process {} was not finished within 180 sec'.format(program)

    log.info("Step: Verify that {} is in DB".format(program))
    assert requests.get(MM_URL.format(program)).status_code == 200,\
        '{} is absent in DB according to MediaManager API'.format(program)


if __name__ == '__main__':
    pytest.main(['-s', '-v'])
