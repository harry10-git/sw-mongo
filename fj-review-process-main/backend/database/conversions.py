
from database.db_types import EmpProjRole


def sheet_to_db_mongo_db_project_type(project_type: EmpProjRole) -> str:
    """Converts project type to db project type"""
    match project_type:
        case EmpProjRole.PARTNER: return "partner"
        case EmpProjRole.STAFF: return "staff"
        case EmpProjRole.MANAGER: return "manager"
        case _: raise Exception(f"Unknown project type: {project_type}")