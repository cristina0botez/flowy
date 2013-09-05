from pyswf.workflow import Workflow, ActivityProxy
from pyswf.client import WorkflowClient


class PrimeTest(Workflow):
    name = 'PrimeTestWorkflow2'
    version = 1

    div = ActivityProxy('Divider2', 1)

    def run(self, n=None):
        n = n if n is not None else 7 * 11
        for i in range(2, n/2):
            if self.div(n, i).result():
                print '%s is divisible by %s' % (n, i)
                break



c = WorkflowClient('SeversTest', 'prime_task_list', [PrimeTest])
c.run()