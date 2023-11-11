from datetime import date, datetime
import pymongo
from config import settings
import pymongo.collection

from database.db_types import EmpProj, Employee, FJClient, Project
import database.conversions as conversions


class ReviewMongoDB():
    def __init__(self) -> None:

        myclient = pymongo.MongoClient(
            "mongodb://mongodb:27017", uuidRepresentation="standard")
        database_name = settings.MONGO_DATABASE if settings.DEPLOYED else settings.TEST_MONGO_DATABASE
        
        if database_name not in myclient.list_database_names():
            myclient[database_name].create_collection(
                "needed_reviews")
            myclient[database_name].create_collection("reviews")
            myclient[database_name].create_collection("employees")
        db = myclient.get_database(database_name)

        self.needed_reviews: pymongo.collection.Collection = db.get_collection(
            "needed_reviews")
        self.reviews: pymongo.collection.Collection = db.get_collection(
            "reviews")
        self.employees: pymongo.collection.Collection = db.get_collection(
            "employees")

    def create_internal_needed_review(self,
                             emp_proj: EmpProj,
                             reviewee: Employee,
                             reviewer_cons_proj: EmpProj,
                             reviewer: Employee,
                             project: Project,
                             due_date: date,
                             ) -> None:
        """Creates a needed review"""
        needed_review = {
            "type": conversions.sheet_to_db_mongo_db_project_type(emp_proj.role),
            "reviewer_id": reviewer.id,
            "reviewer_name": reviewer.emp_name,
            "reviewer_email": reviewer.email_fj,
            "employee_id": reviewee.id,
            "employee_name": reviewee.emp_name,
            "employee_email": reviewee.email_fj,
            "project_id": project.id,
            "reviewer_project_role": conversions.sheet_to_db_mongo_db_project_type(reviewer_cons_proj.role),
            "project_name": project.project_name,
            "due_date": due_date.strftime("%Y-%m-%d"),
            "description": f"Review Project Performance of {reviewee.emp_name} on {project.project_name}",
            "status": "incomplete",
            "created_at": datetime.combine(settings.TODAYS_DATE, datetime.min.time())
        }
        self.needed_reviews.insert_one(needed_review)
        
    def create_external_needed_review(self,
                                      emp_proj: EmpProj,
                                      client_person: FJClient,
                                      reviewee: Employee,
                                      project: Project,
                                      due_date: date,
                                        ) -> None:
        """Creates a needed review"""
        needed_review = {
            "type": "external",
            "reviewer_id": client_person.id,
            "reviewer_name": client_person.client_name,
            "reviewer_email": client_person.email,
            "employee_id": reviewee.id,
            "employee_name": reviewee.emp_name,
            "employee_email": reviewee.email_fj,
            "project_id": project.id,
            "reviewer_project_role": conversions.sheet_to_db_mongo_db_project_type(emp_proj.role),
            "project_name": project.project_name,
            "due_date": due_date.strftime("%Y-%m-%d"),
            "description": f"Review Project Performance of {reviewee.emp_name} on {project.project_name}",
            "status": "incomplete",
            "created_at": datetime.combine(settings.TODAYS_DATE, datetime.min.time())
        }
        self.needed_reviews.insert_one(needed_review)
        
    def create_needed_self_appraisal(self,
                                        employee: Employee,
                                        due_date: date,
                                        ) -> None:
        """Creates a needed self appraisal"""
        needed_review = {
            "type": "self",
            "reviewer_id": employee.id,
            "reviewer_name": employee.emp_name,
            "reviewer_email": employee.email_fj,
            "employee_id": employee.id,
            "employee_name": employee.emp_name,
            "employee_email": employee.email_fj,
            "due_date": due_date.strftime("%Y-%m-%d"),
            "description": "Complete Self Appraisal",
            "status": "incomplete",
            "created_at": datetime.combine(settings.TODAYS_DATE, datetime.min.time())
        }
        self.needed_reviews.insert_one(needed_review)
                                        

    def is_db_internal_type(self, project_type: str) -> bool:
        """Checks if the project type is an internal type"""
        return project_type in ["staff", "manager", "partner"]


mongo_db = ReviewMongoDB()
