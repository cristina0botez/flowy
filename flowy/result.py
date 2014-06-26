from flowy.exception import SuspendTask, TaskError, TaskTimedout


class BaseReturn(object):
    def __lt__(self, other):
        return self._priority < other._priority


class Placeholder(BaseReturn):
    _priority = float("inf")

    def result(self):
        raise SuspendTask()


class Error(BaseReturn):
    def __init__(self, reason, priority):
        self._priority = priority
        self._reason = reason

    def result(self):
        raise TaskError(self._reason)


class Timeout(BaseReturn):
    def __init__(self, priority):
        self._priority = priority

    def result(self):
        raise TaskTimedout()


class Result(BaseReturn):
    def __init__(self, result, priority):
        self._result = result
        self._priority = priority

    def result(self):
        return self._result
