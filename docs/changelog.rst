Changelog
=========


Next Release
------------

* Moved public API components in ``flowy`` module.
* Added ``wait_for`` method on the ``SWFWorkflow`` class. It can be used to
  wait for a task to finish, similar with calling ``.result()`` but without the
  possibility of raising an exception even if error handling is on.
* Changed ``first_n`` and ``all`` to return an iterator that can be used to
  iterate over the finished tasks in order. When the iterator is exhausted and
  more tasks are needed, the workflow is suspended.
* Removed ``fail()`` from the public API of tasks.
* Removed ``schedule_activity()`` and ``schedule_workflow()`` from the public
  API of the workflows.
* Fail the execution on arguments/results serialization/deserialization errors.
* Lazily serialize the proxy arguments, only once, at schedule time.
