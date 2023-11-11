from datetime import date, timedelta
import numpy as np
import emails.pr_emails as emails
from config import settings
import events
import time
from database.mongo_db import mongo_db

def send_final_reminder_emails():
    
    first_mail_date = date(2023,7,1)                #CHANGE THIS AS PER CONVENIENCE
    
    already_sent_emails = []
    for review in mongo_db.needed_reviews.find({
        "review_type": {"$ne": "external"},
        "status": "incomplete",
        "created_at": {"$gte":first_mail_date}
    }):
        
        
        already_sent_emails = [set(already_sent_emails)]
        
        print(
            f"About to send reminder email for {review['type']} review to {review['reviewer_name']}, {review['reviewer_email']}")
        
        if review['reviewer_email'] not in already_sent_emails:
            emails.send_final_strict_reminder_email(
                reviewer_name=review['reviewer_name'],
                reviewer_email=review['reviewer_email']
            )
            
        already_sent_emails.append(review['reviewer_email'])
    

def send_all_needed_reminder_emails():
    """Send reminder emails to all incomplete reviews"""

    WORKDAYS_BETWEEN_REMINDER_AND_START_EMAIL_PROJECT_END = events.WORKDAYS_BEFORE_REMINDER_EMAIL_PROJECT_END - \
        events.WORKDAYS_BEFORE_FIRST_EMAIL_PROJECT_END

    for review in mongo_db.needed_reviews.find({
            "review_type": {"$ne": "external"},
            "status": "incomplete"}):

        if (settings.TODAYS_DATE == np.busday_offset(settings.MOST_RECENT_6MO_DATE, events.WORKDAYS_BEFORE_REMINDER_EMAIL, roll='backward').astype(date) or
                    review['created_at'].date() == np.busday_offset(settings.MOST_RECENT_6MO_DATE, events.WORKDAYS_BEFORE_FIRST_EMAIL_PROJECT_END, roll='backward').astype(date) or
                    (review['created_at'].date(
                    ) + timedelta(WORKDAYS_BETWEEN_REMINDER_AND_START_EMAIL_PROJECT_END) - settings.TODAYS_DATE).days % 7 == 0
                ):

            print(
                f"About to send reminder email for {review['type']} review to {review['reviewer_email']}")

            # clients only get the one email reminder
            if review['type'] == "external" and settings.TODAYS_DATE == np.busday_offset(settings.MOST_RECENT_6MO_DATE, events.WORKDAYS_BEFORE_REMINDER_EMAIL, roll='backward').astype(date):
                emails.send_external_review_reminder_email(
                    client_person_name=review['reviewer_name'],
                    client_person_email=review['reviewer_email'],
                    project_name=review['project_name'],
                    employee_name=review['employee_name'],
                    needed_review_id=review['_id'],
                )
            elif review['type'] == "self":
                emails.send_self_appraisal_reminder_email(
                    reviewer_name=review['reviewer_name'],
                    reviewer_email=review['reviewer_email'],
                    needed_review_id=review['_id'],
                )
            elif review['type'] == "partner" or review['type'] == "manager" or review['type'] == "staff":
                emails.send_project_review_reminder_email(
                    reviewer_name=review['reviewer_name'],
                    reviewer_email=review['reviewer_email'],
                    project_name=review['project_name'],
                    employee_name=review['employee_name'],
                    needed_review_id=review['_id'],
                )
            time.sleep(3)


def send_all_needed_strict_reminder_emails():
    """Send strict emails to all incomplete reviews"""
    if settings.TODAYS_DATE == np.busday_offset(settings.MOST_RECENT_6MO_DATE, events.WORKDAYS_BEFORE_STRICT_EMAIL, roll='backward').astype(date):
        last_day_to_complete = np.busday_offset(
                    settings.MOST_RECENT_6MO_DATE, events.WORKDAYS_BEFORE_DROP_DEAD_DATE - 1, roll='backward').astype(date)
        for review in mongo_db.needed_reviews.find({"status": "incomplete", "type": "self"}):
            emails.send_strict_self_appraisal_reminder_email(
                reviewer_name=review['reviewer_name'],
                reviewer_email=review['reviewer_email'],
                needed_review_id=review['_id'],
                period=settings.PREVIOUS_PERIOD_STRING,
                last_day_to_complete=last_day_to_complete,
            )
        for review in mongo_db.needed_reviews.find({"status": "incomplete", "type": {"$in": ["partner", "manager", "staff"]}}):
            emails.send_strict_project_review_reminder_email(
                reviewer_name=review['reviewer_name'],
                reviewer_email=review['reviewer_email'],
                project_name=review['project_name'],
                period=settings.PREVIOUS_PERIOD_STRING,
                last_day_to_complete=last_day_to_complete,
                employee_name=review['employee_name'],
                needed_review_id=review['_id'],
            )
