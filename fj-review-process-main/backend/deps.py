import pathlib
import pymongo
import pymongo.database

from config import settings
import gspread
from pydrive2.drive import GoogleDrive
from pydrive2.auth import GoogleAuth
from oauth2client.service_account import ServiceAccountCredentials

myclient = pymongo.MongoClient(
    "mongodb://mongodb:27017", uuidRepresentation="standard")
database_name = settings.MONGO_DATABASE if settings.DEPLOYED else settings.TEST_MONGO_DATABASE
if database_name not in myclient.list_database_names():
    myclient[database_name].create_collection("needed_reviews")
    myclient[database_name].create_collection("reviews")
    myclient[database_name].create_collection("employees")

db = myclient.get_database(database_name)
def get_mongo_db() -> pymongo.database.Database: return db


class EmpProjSheetsDB:
    def __init__(self):
        self.service_account = gspread.service_account_from_dict(settings.GOOGLE_SERVICE_ACCOUNT)
        self.person_projects_worksheet = self.service_account.open(settings.EMPLOYEE_PROJECT_DATABASE).worksheet(
            "Consultant - Project")
        self.person_projects = self.person_projects_worksheet.get_all_records()
        self.projects_worksheet = self.service_account.open(settings.EMPLOYEE_PROJECT_DATABASE).worksheet(
            "Projects")
        self.event_logs_worksheet = self.service_account.open(settings.EMPLOYEE_PROJECT_DATABASE).worksheet(
            "ARS Event Log")
        self.employees_worksheet = self.service_account.open(settings.EMPLOYEE_PROJECT_DATABASE).worksheet(
            "Employees")


sheet_db = EmpProjSheetsDB()
def get_sheet_db() -> EmpProjSheetsDB: return sheet_db


auth = GoogleAuth()
scope = 'https://www.googleapis.com/auth/drive'
auth.credentials = ServiceAccountCredentials.from_json_keyfile_dict(settings.GOOGLE_SERVICE_ACCOUNT, scope)

drive = GoogleDrive(auth)
def get_google_drive() -> GoogleDrive: return drive
