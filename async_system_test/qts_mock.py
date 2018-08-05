#!/usr/bin/env python2
# coding=utf-8
import time
import os
import json
from random import randint
import xml.etree.ElementTree as xmlParser
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

_wfe_programs = []


def consume_xml():
    while True:
        time.sleep(randint(1, 60))  # Consume xml file within 60 seconds
        xmls = [f for f in os.listdir('qts_watch_folder') if f.endswith('xml')]
        for x in xmls:
            xml_file = os.path.join('qts_watch_folder', x)
            tree = xmlParser.parse(xml_file)
            root = tree.getroot()
            _wfe_programs.append(WorkflowEngine(root[0].text))
            os.remove(xml_file)


class WorkflowEngine:
    """
    Processing of program for 10-60 seconds in Workflow Engine
    """
    def __init__(self, program):
        self.timeout = time.time() + randint(10, 60)
        self.data = {'name': program, 'program_id': program, 'status': 'running'}

    def get_data(self):
        if time.time() > self.timeout:
            self.data['status'] = 'completed'
        return json.dumps(self.data)


class ApiMock(BaseHTTPRequestHandler):
    """
    Mock of Workflow engine and Media Manager APIs
    """
    def _wfe_processes_mock(self):
        self.send_response(200)
        self.send_header('content-type', 'application/json; charset=utf-8')
        self.end_headers()
        processes = [process.get_data() for process in _wfe_programs]
        self.wfile.write(str(processes).replace("'", ""))

    def _mm_api_mock(self):
        program_name = os.path.basename(self.path)
        programs_in_db = [json.loads(program.get_data())['name'] for program in _wfe_programs if
                          json.loads(program.get_data())['status'] == 'completed']
        if program_name in programs_in_db:
            self.send_response(200)
        else:
            self.send_response(404)

    def do_GET(self):
        if self.path == '/processes':
            self._wfe_processes_mock()
        if self.path.startswith('/entities/program'):
            self._mm_api_mock()

    def log_message(self, format, *args):
        return

if __name__ == '__main__':
    # Put .xml file with <program><name>program_name</name></program> to qts_watch_folder
    qts = Thread(target=consume_xml)
    qts.daemon = True
    qts.start()
    serv = HTTPServer(("localhost", 12345), ApiMock)
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        pass
    serv.server_close()

