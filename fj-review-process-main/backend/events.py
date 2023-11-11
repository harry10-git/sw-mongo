from database.sheet_db import sheet_db

process_dates = sheet_db.process_dates
process_dates_for_project_end = sheet_db.emp_rolls_off_process_dates


workday_counter = 0
WORKDAYS_BEFORE_FIRST_EMAIL = int(
    process_dates[1]["Workdays After Prior Event"])
workday_counter += process_dates[1]["Workdays After Prior Event"]
WORKDAYS_BEFORE_DUE_DATE = process_dates[2]["Workdays After Prior Event"] + workday_counter
WORKDAYS_BETWEEN_FIRST_EMAIL_AND_DUE_DATE = process_dates[2]["Workdays After Prior Event"]
workday_counter += process_dates[2]["Workdays After Prior Event"]
WORKDAYS_BEFORE_REMINDER_EMAIL = process_dates[3]["Workdays After Prior Event"] + workday_counter
workday_counter += process_dates[3]["Workdays After Prior Event"]
WORKDAYS_BEFORE_STRICT_EMAIL = process_dates[4]["Workdays After Prior Event"] + workday_counter
workday_counter += process_dates[4]["Workdays After Prior Event"]
WORKDAYS_BEFORE_DROP_DEAD_DATE = process_dates[5]["Workdays After Prior Event"] + workday_counter
workday_counter += process_dates[5]["Workdays After Prior Event"]
WORKDAYS_BEFORE_READ_WRITE_OFF_DATE = process_dates[6]["Workdays After Prior Event"] + workday_counter

workday_counter = 0
WORKDAYS_BEFORE_FIRST_EMAIL_PROJECT_END = int(process_dates_for_project_end[
    1]["Workdays After Prior Event"])
workday_counter += process_dates_for_project_end[1]["Workdays After Prior Event"]
WORKDAYS_BEFORE_DUE_DATE_PROJECT_END = process_dates_for_project_end[
    2]["Workdays After Prior Event"] + workday_counter
WORKDAYS_BETWEEN_FIRST_EMAIL_AND_DUE_DATE_PROJECT_END = process_dates_for_project_end[
    2]["Workdays After Prior Event"]
workday_counter += process_dates_for_project_end[2]["Workdays After Prior Event"]
WORKDAYS_BEFORE_REMINDER_EMAIL_PROJECT_END = process_dates_for_project_end[
    3]["Workdays After Prior Event"] + workday_counter
workday_counter += process_dates_for_project_end[3]["Workdays After Prior Event"]
WORKDAYS_BEFORE_STRICT_EMAIL_PROJECT_END = process_dates_for_project_end[
    4]["Workdays After Prior Event"] + workday_counter
workday_counter += process_dates_for_project_end[4]["Workdays After Prior Event"]
WORKDAYS_BEFORE_READ_WRITE_OFF_DATE_PROJECT_END = process_dates_for_project_end[
    5]["Workdays After Prior Event"] + workday_counter
