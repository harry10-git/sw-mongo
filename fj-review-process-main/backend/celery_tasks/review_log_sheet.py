import emails.pr_emails as emails
from database.sheet_db import sheet_db
import pandas as pd
from database.mongo_db import mongo_db
import gspread_dataframe


def update_review_log_sheet():
    reviews_log = pd.DataFrame()
    for review in mongo_db.needed_reviews.find({"status": {"$in": ["completed", "incomplete"]}}):
        if review["type"] == 'self':
            new_row = {'Form ID': review['_id'], 'Project': '', 'Reviewer': review['reviewer_name'], 'Reviewee': review['employee_name'],
                       'Date the first Review Mail was sent': review['created_at'].date(),
                       'Status as of Today': review['status']}
        else:
            new_row = {'Form ID': review['_id'], 'Project': review['project_name'], 'Reviewer': review['reviewer_name'],
                       'Reviewee': review['employee_name'],
                       'Date the first Review Mail was sent': review['created_at'].date(),
                       'Status as of Today': review['status']}

        # concat new row to reviews_log
        reviews_log = pd.concat(
            [reviews_log, pd.DataFrame(new_row, index=[0])], ignore_index=True)

    sheet_db._reviews_log_worksheet.clear()
    gspread_dataframe.set_with_dataframe(
        worksheet=sheet_db._reviews_log_worksheet, dataframe=reviews_log, include_index=False, include_column_header=True)
