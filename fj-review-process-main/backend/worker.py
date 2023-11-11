from datetime import date
import numpy as np
import drive
from config import DropDeadDateFlavor, settings
from celery_app import celery_app
import celery_tasks
import events


@celery_app.task(acks_late=True)
def test_celery(word: str) -> str:
    return f"test task return {word}"


@celery_app.task(acks_late=True)
def daily_run(flavor: DropDeadDateFlavor | None = None):
    create_and_send_new_needed_reviews()
    send_all_needed_reminder_emails()
    send_all_needed_strict_reminder_emails()
    if settings.TODAYS_DATE == np.busday_offset(settings.MOST_RECENT_6MO_DATE, events.WORKDAYS_BEFORE_DROP_DEAD_DATE, roll='backward').astype(date):
        if flavor is not None:
            execute_drop_dead_date(settings.DROP_DEAD_DATE_FLAVOR)
        else:
            execute_drop_dead_date(settings.DROP_DEAD_DATE_FLAVOR)
    send_project_end_date_reminder_email_to_partners()


@celery_app.task(acks_late=True)
def create_and_send_new_needed_reviews() -> None:
    celery_tasks.create_and_send_new_needed_reviews()


@celery_app.task(acks_late=True)
def send_all_needed_reminder_emails() -> None:
    celery_tasks.send_all_needed_reminder_emails()


@celery_app.task(acks_late=True)
def send_all_needed_strict_reminder_emails() -> None:
    celery_tasks.send_all_needed_strict_reminder_emails()

@celery_app.task(acks_late=True)
def send_final_reminder_emails() -> None:
    celery_tasks.send_final_reminder_emails()

@celery_app.task(acks_late=True)
def execute_drop_dead_date(flavor: DropDeadDateFlavor) -> None:
    celery_tasks.execute_drop_dead_date(flavor)


@celery_app.task(acks_late=True)
def send_project_end_date_reminder_email_to_partners() -> None:
    if settings.TODAYS_DATE.weekday() == 0:
        celery_tasks.send_project_end_date_reminder_email_to_partners()


@celery_app.task(acks_late=True)
def update_review_log_sheet() -> None:
    celery_tasks.update_review_log_sheet()


@celery_app.task(acks_late=True)
def turn_off_read_write_access() -> None:
    if settings.TODAYS_DATE == np.busday_offset(settings.MOST_RECENT_6MO_DATE, events.WORKDAYS_BEFORE_READ_WRITE_OFF_DATE, roll='backward').astype(date):
        drive.delete_all_file_permissions_of_file_recursively(
            settings.ALL_EMPLOYEES_DRIVE_FOLDER_ID)
