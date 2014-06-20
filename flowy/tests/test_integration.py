import json
import os
import pprint
import random
import string
import unittest

from boto.swf.layer1 import Layer1
from boto.swf.exceptions import SWFResponseError, SWFTypeAlreadyExistsError
from mock import patch
from flowy import MagicBind


class MockLayer1(Layer1):

    def __init__(self, responses, requests):
        self.responses = iter(responses)
        self.requests = iter(requests)

    def json_request(self, action, data, object_hook=None):
        self._normalize_request_dict(data)
        nxt_req = next(self.requests)
        a, b = pprint.pformat(nxt_req[0]), pprint.pformat(action)
        assert nxt_req[0] == action, ('Difference expected:\n%s\nBut got:\n%s'
                                      % (a, b))
        a, b = pprint.pformat(nxt_req[1]), pprint.pformat(data)
        assert nxt_req[1] == data, 'Expected:\n%s\nBut got:\n%s' % (a, b)
        nxt_resp = next(self.responses)
        try:
            if nxt_resp.strip() == 'SWFResponseError':
                raise SWFResponseError(None, None)
            if nxt_resp.strip() == 'SWFTypeAlreadyExistsError':
                raise SWFTypeAlreadyExistsError(None, None)
        except AttributeError:
            pass
        return nxt_resp


def make(file_name, fut):
    f = open(os.path.join(here, 'wlogs', file_name))
    responses = []
    requests = []
    for line in f:
        line = line.split('\t')
        if line[0] == '<<<':
            res = line[1]
            try:
                res = json.loads(res)
            except ValueError:
                pass
            responses.append(res)
        else:
            requests.append((line[1], json.loads(line[2])))
    f.close()

    @patch('uuid.uuid4')
    def test(self, uuid):
        random.seed(0)
        uuid.return_value = ''.join(random.choice(string.ascii_uppercase +
                                    string.digits) for x in range(10))
        mock_layer1 = MagicBind(MockLayer1(responses, requests),
                                domain='IntegrationTest')
        fut(mock_layer1, responses, requests)
    return test


class ExamplesTest(unittest.TestCase):
    pass


def run_workflow(layer1, responses, requests):
    from flowy.boilerplate import start_workflow_worker
    from flowy.tests import workflows
    start_workflow_worker('IntegrationTest', 'example_list',
                          layer1=layer1,
                          reg_remote=False,
                          package=workflows,
                          loop=len(requests) / 2)


here = os.path.dirname(__file__)

for file_name in os.listdir(os.path.join(here, 'wlogs')):
    test_name = 'test_' + file_name.rsplit('.', 1)[0]
    setattr(ExamplesTest, test_name, make(file_name, run_workflow))


def run_workflow_registration(layer1, responses, requests):
    from flowy.scanner import SWFScanner
    from flowy.tests import workflows
    scanner = SWFScanner()
    scanner.scan_workflows(package=workflows)
    assert scanner.register_remote(layer1) == []


def run_activity_registration(layer1, responses, requests):
    from flowy.scanner import SWFScanner
    from flowy.tests import activities
    scanner = SWFScanner()
    scanner.scan_activities(package=activities)
    assert scanner.register_remote(layer1) == []


class RegistrationTest(unittest.TestCase):
    test_workflow_registration = make(os.path.join(here, 'rlogs/w.log'),
                                      run_workflow_registration)
    test_activity_registration = make(os.path.join(here, 'rlogs/a.log'),
                                      run_activity_registration)
