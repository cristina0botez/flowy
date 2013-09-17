import unittest


class WorkflowResponseTest(unittest.TestCase):

    def _get_uut(self, client):
        from pyswf.client import WorkflowResponse
        return WorkflowResponse(client)

    def test_name_version(self):

        class Client(object):
            def poll(self):
                return{'workflowType': {'name': 'Name', 'version': '123'}}

        workflow_response = self._get_uut(Client())
        self.assertEqual('Name', workflow_response.name)
        self.assertEqual('123', workflow_response.version)

    def test_scheduled_activities(self):
        dummy_client = DummyClient(t='token')
        workflow_response = self._get_uut(dummy_client)
        workflow_response.schedule('call1', 'activity1', 'v1', 'input1')
        workflow_response.schedule('call2', 'activity2', 'v2', 'input2')
        workflow_response.suspend('context')
        self.assertEqual(set([
            ('call1', 'activity1', 'v1', 'input1'),
            ('call2', 'activity2', 'v2', 'input2'),
        ]), dummy_client.scheduled)
        self.assertEqual('context', dummy_client.context)
        self.assertEqual('token', dummy_client.token)

    def test_no_scheduled_activities(self):
        dummy_client = DummyClient(t='token')
        workflow_response = self._get_uut(dummy_client)
        workflow_response.suspend('context')
        self.assertEqual(set(), dummy_client.scheduled)
        self.assertEqual('context', dummy_client.context)
        self.assertEqual('token', dummy_client.token)

    def test_complete_workflow(self):
        dummy_client = DummyClient(t='token')
        workflow_response = self._get_uut(dummy_client)
        workflow_response.complete('result')
        self.assertEqual('result', dummy_client.result)
        self.assertEqual('token', dummy_client.token)


class WorkflowNewEventsTest(unittest.TestCase):

    def _get_uut(self, client):
        from pyswf.client import WorkflowResponse
        return WorkflowResponse(client)

    def test_first_few_events(self):
        dummy_client = DummyClient()
        for _ in range(4):
            dummy_client.add_dummy_event()
        workflow_response = self._get_uut(dummy_client)
        self.assertEqual(len(list(workflow_response.new_events)), 4)

    def test_paginated_new_events(self):
        dummy_client = DummyClient(page_size=3)
        for _ in range(8):
            dummy_client.add_dummy_event()
        workflow_response = self._get_uut(dummy_client)
        self.assertEqual(len(list(workflow_response.new_events)), 8)

    def test_first_few_new_events(self):
        dummy_client = DummyClient(previous_started_event_id='3')
        for _ in range(5):
            dummy_client.add_dummy_event()
        workflow_response = self._get_uut(dummy_client)
        self.assertEqual(len(list(workflow_response.new_events)), 3)

    def test_first_few_paginated_new_events(self):
        dummy_client = DummyClient(page_size=3, previous_started_event_id='13')
        for _ in range(18):
            dummy_client.add_dummy_event()
        workflow_response = self._get_uut(dummy_client)
        self.assertEqual(len(list(workflow_response.new_events)), 13)

    def test_no_new_events(self):
        dummy_client = DummyClient()
        workflow_response = self._get_uut(dummy_client)
        self.assertEqual(len(list(workflow_response.new_events)), 0)


class WorkflowContextTest(unittest.TestCase):

    def _get_uut(self, client):
        from pyswf.client import WorkflowResponse
        return WorkflowResponse(client)

    def test_no_context(self):
        dummy_client = DummyClient()
        for _ in range(4):
            dummy_client.add_dummy_event()
        workflow_response = self._get_uut(dummy_client)
        self.assertEqual(workflow_response.context, None)

    def test_no_context_paginated(self):
        dummy_client = DummyClient()
        for _ in range(44):
            dummy_client.add_dummy_event()
        workflow_response = self._get_uut(dummy_client)
        self.assertEqual(workflow_response.context, None)

    def test_context(self):
        dummy_client = DummyClient(previous_started_event_id='5')
        dummy_client.add_dummy_event()
        dummy_client.add_decision_completed('context', '4', '3')
        for _ in range(5):
            dummy_client.add_dummy_event()
        workflow_response = self._get_uut(dummy_client)
        self.assertEqual(workflow_response.context, 'context')

    def test_context_paginated(self):
        dummy_client = DummyClient(previous_started_event_id='20', page_size=5)
        for _ in range(13):
            dummy_client.add_dummy_event()
        dummy_client.add_decision_completed('context', '4', '3')
        for _ in range(12):
            dummy_client.add_dummy_event()
        workflow_response = self._get_uut(dummy_client)
        self.assertEqual(workflow_response.context, 'context')


class DummyClient(object):
    def __init__(self, previous_started_event_id=None, page_size=10, t=None):
        self.page_size = page_size
        self.events = []
        self.next_page_token = None
        self.next_start = 0
        self.previous_started_event_id = previous_started_event_id
        self.token = t
        self.id = 0

    def add_event(event):
        self.events.append(event)

    def add_decision_completed(self, context, scheduled_id, started_id):
        d = {
            'eventType': 'DecisionTaskCompleted',
            'eventTimestamp': 1234567,
            'eventId': str(self.id),
            'decisionTaskCompletedEventAttributes': {
                'executionContext': context,
                'scheduledEventId': scheduled_id,
                'startedEventId': started_id
            }
        }
        self.id += 1
        self.events.append(d)

    def add_dummy_event(self):
        d = {
            'eventType': 'Dummy',
            'eventTimestamp': 1234567,
            'eventId': str(self.id),
        }
        self.id += 1
        self.events.append(d)

    def schedule_activities(self, token, scheduled, context):
        self.token = token
        self.scheduled = set(scheduled)
        self.context = context

    def complete_workflow(self, token, result):
        self.token = token
        self.result = result

    def poll(self, next_page_token=None):
        if not next_page_token == self.next_page_token:
            raise AssertionError('Invalid page token')
        r = self.events[self.next_start:self.next_start + self.page_size]
        self.next_start += self.page_size
        self.next_page_token = 'token_%s' % (self.next_start / self.page_size)
        page =  {
            'events': r,
        }
        if len(self.events) > self.next_start:
            page['nextPageToken'] = self.next_page_token
        if self.previous_started_event_id is not None:
            page['previousStartedEventId'] = self.previous_started_event_id
        if self.token:
            page['taskToken'] = self.token
        return page
