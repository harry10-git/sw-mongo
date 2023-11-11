from enum import StrEnum
from pydrive2.drive import GoogleDrive, GoogleDriveFile
from pydrive2.auth import GoogleAuth
from oauth2client.service_account import ServiceAccountCredentials

from config import settings

auth = GoogleAuth()
scope = 'https://www.googleapis.com/auth/drive'
auth.credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    settings.GOOGLE_SERVICE_ACCOUNT, scope)

drive = GoogleDrive(auth)


def delete_all_file_permissions_of_file_recursively(folder_id: str):
    all_files: list[GoogleDriveFile] = drive.ListFile(
        {'q': f"'{folder_id}' in parents and trashed=false"}).GetList()
    for file in all_files:
        for permission in file.GetPermissions():
            if permission['role'] != 'owner':
                file.DeletePermission(permission['id'])


class FileType(StrEnum):
    FOLDER = "application/vnd.google-apps.folder"
    GOOGLE_SHEET = "application/vnd.google-apps.spreadsheet"
    FILE = "application/vnd.google-apps.file"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def create_file(file_name: str, parent_folder_id: str, file_type: FileType, file_path: str | None = None, file_content: str | None = None) -> str:
    params = {'title': file_name,
              'mimeType': file_type,
              'parents': [{'id': parent_folder_id}]}
    if file_path:
        file = drive.CreateFile(params)
        file.SetContentFile(file_path)
    elif file_content:
        file = drive.CreateFile(params)
        file.SetContentString(file_content)
    else:
        file = drive.CreateFile(params)
    file.Upload()
    remove_all_permissions_but_owner(file)
    return file['id']


class PermissionRole(StrEnum):
    READER = "reader"
    WRITER = "writer"
    COMMENTER = "commenter"
    OWNER = "owner"
    ORGANIZER = "organizer"


def set_permission(file_id: str, email: str, role: PermissionRole):
    # GIVE THE USER access of the specified role and set
    file = drive.CreateFile({'id': file_id})
    permission = file.InsertPermission(
        {
            'type': 'user',
            'value': email,
            'role': role,
        },
        {'sendNotificationEmails': False, 'emailMessage': ''}
    )
    return permission


def remove_all_permissions_but_owner(file: GoogleDriveFile):
    for permission in file.GetPermissions():
        if permission['role'] != 'owner' and permission['emailAddress'] != settings.DRIVE_OWNER_EMAIL:
            file.DeletePermission(permission['id'])
