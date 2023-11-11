from dataclasses import dataclass
from enum import StrEnum
import pandas as pd
import requests
from config import settings


class KMSProjectCol(StrEnum):
    id = "id"
    url = "url"
    collaborator_emails_comma_sep = "collaborator_emails"
    created_on = "created_on"
    title_str = "title"
    
class KMS_API:
    """Wrapper for all io with the fischer jordan's knowledge management system"""

    def __init__(self):
        self.auth_headers = {
            "Content-Type": "application/json",
            "Authorization": "Token " + settings.KMS_TOKEN,
        }
        self.all_projects: pd.DataFrame|None = None

    def get_projects(self, limit:int=10, offset:int=0) -> list[dict]:
        """Get the library of projects"""

        query: str = f"?limit={limit}&offset={offset}"

        response = requests.get(f'https://fj.orangeyak.xyz/api/core/projects/{query}',
                                headers=self.auth_headers)

        return response.json().get("results", [])

    def get_all_projects_with_colab_emails(self, limit) -> pd.DataFrame:
        """Get all projects with collaborator emails"""
        if not self.all_projects is None:
            return self.all_projects
        projects = self.get_projects(limit=limit)
        self.all_projects=pd.DataFrame()
        for project in projects:
            # add a row to the dataframe
            self.all_projects = self.all_projects.append(pd.DataFrame({ # type: ignore
                KMSProjectCol.id: [project["id"]],
                KMSProjectCol.url: [f'https://kms.fischerjordan.com/project/{project["id"]}/'],
                KMSProjectCol.collaborator_emails_comma_sep: [','.join([colab["username"] for colab in project["collaborators"]])],
                KMSProjectCol.created_on: [project["created_on"]],
                KMSProjectCol.title_str: [project["title"]],
            }))
            
        return self.all_projects
    
    def get_projects_for_employee(self, email:str)-> pd.DataFrame:
        """Get all projects for a given employee"""
        kms_projects = self.get_all_projects_with_colab_emails(limit=1000)
        return kms_projects[kms_projects[KMSProjectCol.collaborator_emails_comma_sep].str.contains(email)]
        


if __name__ == "__main__":
    kms = KMS_API()

    # test get all projects with colab emails
    all = kms.get_all_projects_with_colab_emails(limit=100)

    # convert to pandas df
    import pandas as pd
    df = pd.DataFrame(all)
    print(df)
