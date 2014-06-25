from flowy.exception import SuspendTask, TaskError, TaskTimedout


class Placeholder(object):
    def result(self):
        raise SuspendTask()


class Error(object):
    def __init__(self, reason):
        self._reason = reason

    def result(self):
        raise TaskError(self._reason)


class Timeout(object):
    def result(self):
        raise TaskTimedout()


class Result(object):
    def __init__(self, result, call_id):
        self._result = result
        self.id = call_id

    def result(self):
        return self._result
