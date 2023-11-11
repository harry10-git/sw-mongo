# fj-review-process
A python back end for the automated review process for info for employee performance

## Development
docker compose -f docker-compose.dev.yml up -d --build --remove-orphans

## To manually run a task
docker exec fj-review-process-celeryworker-1 python manage/run_celery_task.py create_and_send_new_needed_reviews