from datetime import date, datetime
from enum import StrEnum
from pydantic import AnyHttpUrl, EmailStr, validator
from pydantic_settings import BaseSettings


class DropDeadDateFlavor(StrEnum):
    FORMAL = "formal"
    INFORMAL = "informal"


class Settings(BaseSettings):

    EMPLOYEE_PROJECT_DATABASE: str
    DEPLOYED: bool

    @validator("DEPLOYED", pre=True, allow_reuse=True)
    def validate_deployed(cls, v):
        if v.lower() not in ["true", "false"]:
            raise ValueError("DEPLOYED must be either 'true' or 'false'")
        return v.lower() == "true"

    TEST_TODAYS_DATE: str|None = None

    BACKUP_FOLDER_ID: str
    TEST_EMAIL: EmailStr
    SETTINGS_SHEET_NAME: str
    APP_URL: AnyHttpUrl

    MONGO_DATABASE: str
    DRIVE_OWNER_EMAIL: EmailStr
    TEST_MONGO_DATABASE: str
    ALL_EMPLOYEES_DRIVE_FOLDER_ID: str
    OFFLINE_TRAINING_SHEET_NAME: str
    KMS_TOKEN: str
    ONLINE_TRAINING_SHEET_NAME: str
    GOOGLE_SERVICE_ACCOUNT: dict[str, str]
    CALENDAR_SERVICE_ACCOUNT: dict[str, str]
    
    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str

    CODE_ADMIN_EMAILS: list[EmailStr]
    
    WRITE_ACCESS_EMAIL: EmailStr
    ALWAYS_REVIEW_MEETING_EMAILS: list[EmailStr]
    ALWAYS_REVIEW_MEETING_NAMES: list[str]
    RECRUITMENT_AND_STAFFING_ID: str
    EMPLOYEE_PROJECT_DATABASE_SHEET_NAME: str
    SCHEDULER_NAME: str
    NO_REVIEW_MEETING_EMPLOYEE_NAMES: list[str]
    STRICT_EMAIL_CC: list[EmailStr]
    MINIMUM_TEAMMATES_OVERLAP_TIME_DAYS: int
    SCHEDULER_EMAIL: EmailStr
    

    @property
    def MOST_RECENT_6MO_DATE(self) -> date:
        return date(self.TODAYS_DATE.year, 7, 1) if self.TODAYS_DATE.month >= 7 else date(self.TODAYS_DATE.year - 1, 7, 1)
    
    @property
    def NEXT_6MO_DATE(self) -> date:
        return date(self.TODAYS_DATE.year + 1, 1, 1) if self.TODAYS_DATE.month >= 7 else date(self.TODAYS_DATE.year, 1, 1)

    MANUAL_DROP_DEAD_DATE_FLAVOR: str|None = None

    @validator("MANUAL_DROP_DEAD_DATE_FLAVOR", pre=True, allow_reuse=True)
    def validate_drop_dead_date_flavor(cls, v):
        if v not in [DropDeadDateFlavor.FORMAL, DropDeadDateFlavor.INFORMAL, "", None]:
            raise ValueError(
                f"MANUAL_DROP_DEAD_DATE_FLAVOR must be either '{DropDeadDateFlavor.FORMAL}' or '{DropDeadDateFlavor.INFORMAL}'")
        return v
    
    @property
    def DROP_DEAD_DATE_FLAVOR(self) -> DropDeadDateFlavor:
        if self.MANUAL_DROP_DEAD_DATE_FLAVOR is not None:
            return DropDeadDateFlavor(self.MANUAL_DROP_DEAD_DATE_FLAVOR)
        elif self.TODAYS_DATE.month in [1, 2, 3, 4, 5, 6]:
            return DropDeadDateFlavor.FORMAL
        else:
            return DropDeadDateFlavor.INFORMAL
    
    @property
    def TODAYS_DATE(self) -> date:
        if self.DEPLOYED:
            return date.today()
        elif self.TEST_TODAYS_DATE is None:
            raise ValueError("TEST_TODAYS_DATE must be set if DEPLOYED is False")
        else:
            return datetime.strptime(self.TEST_TODAYS_DATE, "%Y-%m-%d").date()
        
    @property
    def PREVIOUS_PERIOD_STRING(self) -> str:
        if self.TODAYS_DATE.month in [1, 2, 3, 4, 5, 6]:
            return f"2H-{self.TODAYS_DATE.year-1}"
        else:
            return f"1H-{self.TODAYS_DATE.year}"

    class Config:
        env_file = f".env"
        case_sensitive = True


settings: Settings = Settings()  # type: ignore
