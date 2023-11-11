import sys
from celery.result import AsyncResult
from celery_app import celery_app
import worker as worker


# use python arguments to pass to celery task where the first argument is the task name

arg1 = sys.argv[1]

result = worker.__dict__[arg1].delay(*sys.argv[2:])
task_id = result.task_id
print(f"task_id: {task_id}")
result = AsyncResult(task_id)
print(f"result: {result.get()}")

