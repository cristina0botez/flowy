import json
from contextlib import contextmanager

from flowy.exception import TaskError
from flowy.result import Error
from flowy.result import Placeholder
from flowy.result import Result
from flowy.result import Timeout
from flowy.spec import _sentinel
from flowy.spec import SWFActivitySpec
from flowy.spec import SWFWorkflowSpec
from flowy.task import serialize_args
from flowy.util import MagicBind

deserialize_result = staticmethod(json.loads)


class TaskProxy(object):

    Error = Error
    Placeholder = Placeholder
    Result = Result
    Timeout = Timeout

    timeout_message = "A task has timed-out"

    def __init__(self, retry=3, delay=0, error_handling=False):
        self._retry = retry
        self._delay = delay
        self._error_handling = error_handling

    def __get__(self, obj, objtype):
        if obj is None:
            return self
        return MagicBind(self, workflow=obj)

    @contextmanager
    def options(self, retry=_sentinel, delay=_sentinel,
                error_handling=_sentinel):
        old_retry = self._retry
        old_delay = self._delay
        old_error_handling = self._error_handling
        if retry is not _sentinel:
            self._retry = retry
        if delay is not _sentinel:
            self._delay = delay
        if error_handling is not _sentinel:
            self._error_handling = error_handling
        yield
        self._retry = old_retry
        self._delay = old_delay
        self._error_handling = old_error_handling

    def __call__(self, workflow, *args, **kwargs):
        result = self._args_based_result(workflow, args, kwargs)
        if result is not None:
            return result
        def lazy_input():
            args_, kwargs_ = self._extract_results(args, kwargs)
            return self._serialize_arguments(*args_, **kwargs_)
        state, value, order = self._schedule(workflow, lazy_input)
        if state == workflow._FOUND:
            try:
                d_result = self._deserialize_result(value)
            except Exception as e:
                workflow._fail(e)
                return Placeholder()
            return self.Result(d_result, order)
        elif state == workflow._RUNNING:
            return self.Placeholder()
        elif state == workflow._ERROR:
            if self._error_handling:
                return self.Error(value, order)
            workflow._fail(value)
            return self.Placeholder()
        elif state == workflow._TIMEDOUT:
            if self._error_handling:
                return self.Timeout(self.timeout_message, order)
            workflow._fail(self.timeout_message)
            return self.Placeholder()

    def _args_based_result(self, workflow, args, kwargs):
        args = tuple(args) + tuple(kwargs.values())
        errs = [e for e in args if isinstance(e, (Error, Timeout))]
        if errs:
            first_e = min(errs)
            error_message = self._err_message(errs)
            if self._error_handling:
                # Same order as the first error in the arguments
                return self.Error(error_message, first_e._order)
            else:
                workflow._fail(error_message)
                return self.Placeholder()
        if self._deps_in_args(args):
            return self.Placeholder()

    def _deps_in_args(self, args):
        return any(isinstance(r, Placeholder) for r in args)

    def _err_message(self, errs):
        msg = []
        for e in errs:
            try:
                e.result()
            except TaskError as te:
                msg.append(str(te))
        return '\n'.join(msg)

    def _extract_results(self, args, kwargs):
        a = [arg.result() if isinstance(arg, Result)
             else arg for arg in args]
        k = dict((k, v.result() if isinstance(v, Result) else v)
                 for k, v in kwargs.items())
        return a, k

    _serialize_arguments = serialize_args
    _deserialize_result = deserialize_result


class SWFActivityProxy(TaskProxy):
    def __init__(self, name, version, task_list=None, heartbeat=None,
                 schedule_to_close=None, schedule_to_start=None,
                 start_to_close=None, retry=3, delay=0, error_handling=False):
        self._spec = SWFActivitySpec(name, version, task_list, heartbeat,
                                     schedule_to_close, schedule_to_start,
                                     start_to_close)
        self.timeout_message = "Activity %s has timed-out" % self._spec
        super(SWFActivityProxy, self).__init__(retry, delay, error_handling)

    @contextmanager
    def options(self, task_list=_sentinel, heartbeat=_sentinel,
                schedule_to_close=_sentinel, schedule_to_start=_sentinel,
                start_to_close=_sentinel, retry=_sentinel, delay=_sentinel,
                error_handling=_sentinel):
        with self._spec.options(task_list, heartbeat, schedule_to_close,
                                schedule_to_start, start_to_close):
            with super(SWFActivityProxy, self).options(retry, delay,
                                                       error_handling):
                yield

    def _schedule(self, workflow, lazy_input):
        return workflow._schedule_activity(self._spec, lazy_input, self._retry,
                                           self._delay)


class SWFWorkflowProxy(TaskProxy):
    def __init__(self, name, version, task_list=None, decision_duration=None,
                 workflow_duration=None, retry=3, delay=0,
                 error_handling=False):
        self._spec = SWFWorkflowSpec(name, version, task_list,
                                     decision_duration, workflow_duration)
        self.timeout_message = "Workflow %s has timed-out" % self._spec
        super(SWFWorkflowProxy, self).__init__(retry, delay, error_handling)

    @contextmanager
    def options(self, task_list=_sentinel, decision_duration=_sentinel,
                workflow_duration=_sentinel, retry=_sentinel, delay=_sentinel,
                error_handling=_sentinel):
        with self._spec.options(task_list, decision_duration,
                                workflow_duration):
            with super(SWFWorkflowProxy, self).options(retry, delay,
                                                       error_handling):
                yield

    def _schedule(self, workflow, lazy_input):
        return workflow._schedule_workflow(self._spec, lazy_input, self._retry,
                                           self._delay)
