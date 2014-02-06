import json
import logging
from functools import partial

from flowy import posint_or_none, str_or_none


class SuspendTask(Exception):
    """ Raised to suspend the task run.

    This happens when a worklfow needs to wait for an activity or in case of an
    async activity.
    """


class TaskError(Exception):
    """ Raised from an activity or subworkflow task if error handling is
    enabled and the task fails.
    """


class TaskTimedout(TaskError):
    """ Raised from an activity or subworkflow task if any of its timeout
    timers were exceeded.
    """


class Task(object):
    def __init__(self, input, scheduler):
        self._input = str(input)
        self._scheduler = scheduler

    def __call__(self):
        try:
            args, kwargs = self._deserialize_arguments()
            result = self.run(*args, **kwargs)
        except SuspendTask:
            self._scheduler.suspend()
        except Exception as e:
            self._scheduler.fail(str(e))
            logging.exception("Error while running the task:")
        else:
            self._scheduler.complete(self._serialize_result(result))

    def run(self, *args, **kwargs):
        raise NotImplementedError  # pragma: no cover

    def _serialize_result(self, result):
        return json.dumps(result)

    def _deserialize_arguments(self):
        return json.loads(self._input)


class Activity(Task):
    def heartbeat(self):
        return self._scheduler.heartbeat()


class Workflow(Task):
    def options(self, **kwargs):
        self._scheduler.options(**kwargs)

    def restart(self, *args, **kwargs):
        arguments = self._serialize_restart_arguments(*args, **kwargs)
        return self._scheduler.restart(arguments)

    def _serialize_restart_arguments(self, *args, **kwargs):
        return json.dumps([args, kwargs])


class TaskProxy(object):
    def __get__(self, obj, objtype):
        if obj is None:
            return self
        if not hasattr(obj, '_scheduler'):
            raise AttributeError('no scheduler bound to the task')
        return partial(self, obj._scheduler)

    def _serialize_arguments(self, *args, **kwargs):
        return json.dumps([args, kwargs])

    def _deserialize_result(self, result):
        return json.loads(result)


class ActivityProxy(TaskProxy):
    def __init__(self, task_id,
                 heartbeat=None,
                 schedule_to_close=None,
                 schedule_to_start=None,
                 start_to_close=None,
                 task_list=None,
                 retry=3,
                 delay=0,
                 error_handling=False):
        self._kwargs = dict(
            task_id=task_id,
            heartbeat=posint_or_none(heartbeat),
            schedule_to_close=posint_or_none(schedule_to_close),
            schedule_to_start=posint_or_none(schedule_to_start),
            start_to_close=posint_or_none(start_to_close),
            task_list=str_or_none(task_list),
            retry=max(int(retry), 0),
            delay=max(int(delay), 0),
            error_handling=bool(error_handling)
        )

    def __call__(self, scheduler, *args, **kwargs):
        return scheduler.remote_activity(
            args=args, kwargs=kwargs,
            args_serializer=self._serialize_arguments,
            result_deserializer=self._deserialize_result,
            **self._kwargs
        )


class WorkflowProxy(TaskProxy):
    def __init__(self, task_id,
                 decision_duration=None,
                 workflow_duration=None,
                 task_list=None,
                 retry=3,
                 delay=0,
                 error_handling=False):
        self._kwargs = dict(
            task_id=task_id,
            decision_duration=posint_or_none(decision_duration),
            workflow_duration=posint_or_none(workflow_duration),
            task_list=str_or_none(task_list),
            retry=max(int(retry), 0),
            delay=max(int(delay), 0),
            error_handling=bool(error_handling)
        )

    def __call__(self, scheduler, *args, **kwargs):
        return scheduler.remote_subworkflow(
            args=args, kwargs=kwargs,
            args_serializer=self._serialize_arguments,
            result_deserializer=self._deserialize_result,
            **self._kwargs
        )