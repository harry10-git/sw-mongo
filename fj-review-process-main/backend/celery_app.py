from celery import Celery
from celery.schedules import crontab
from celery.signals import after_setup_logger
import logging

celery_app = Celery("worker",
                    backend="redis://redis:6379",
                    broker="redis://redis:6379",
                    )
celery_app.conf.task_routes = {
    "worker.test_celery": "main-queue",
    "worker.daily_run": "main-queue",
    "worker.create_and_send_new_needed_reviews": "main-queue",
    "worker.send_all_needed_reminder_emails": "main-queue",
    "worker.send_all_needed_strict_reminder_emails": "main-queue",
    "worker.send_final_reminder_emails":"main_queue",
    "worker.execute_drop_dead_date": "main-queue",
    "worker.send_project_end_date_reminder_email_to_partners": "main-queue",
    "worker.update_review_log_sheet": "main-queue",
    "worker.turn_off_read_write_access": "main-queue",
}

@after_setup_logger.connect
def setup_loggers(logger, *args, **kwargs):
    my_handler = logging.StreamHandler()
    my_handler.setLevel(logging.DEBUG)
    my_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    my_handler.setFormatter(my_formatter)
    logger.addHandler(my_handler)
    
# @celery_app.on_after_configure.connect # type: ignore
# def setup_periodic_tasks(sender, **kwargs):
#     sender.add_periodic_task(
#         crontab(minute="*/1"),
#         worker.test_celery.s("hello"),
#         name="test every minute",
#     )
