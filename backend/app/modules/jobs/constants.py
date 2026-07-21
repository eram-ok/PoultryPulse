from enum import StrEnum


class BackgroundJobName(StrEnum):
    ALERT_REFRESH = "alert_refresh"
    NOTIFICATION_DELIVERY = "notification_delivery"
    JOB_HISTORY_CLEANUP = "job_history_cleanup"


class BackgroundJobStatus(StrEnum):
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class BackgroundJobTrigger(StrEnum):
    SCHEDULED = "SCHEDULED"
    MANUAL = "MANUAL"
