import json
from dataclasses import dataclass
from enum import Enum
from typing import Dict


class RtnStatus(Enum):
    NOT_SET = "<Not_set>"
    FATAL = "FATAL"
    FAIL = "Fail"
    WARNING = "Warning"
    SUCCESS = "Success"


@dataclass(order=True)
class Result:
    """
    Easy way to create function safe call result return.

    stage: the name or info of the calling method. Readable.
           Will auto generate by class name if not set.
    status: the result status, success or fail. Only key to do match.
    detail: the return or error message, should be readable dict | str. Readable.

    """

    stage: str = 'Result'
    status: RtnStatus = RtnStatus.NOT_SET
    detail: dict | str = "Nothing to say here."

    def __post_init__(self):
        # Set proper stage
        self.stage = self.__class__.__name__
        if self.stage == 'Result':
            self.stage = 'UNKNOWN'  # if class is Result, set to UNKNOWN

    def fatal(self, message: str | dict):
        """Create a fatal respond with detail=message."""
        self.status = RtnStatus.FATAL
        self.detail = message
        return self.to_json()

    def fail(self, message: str | dict):
        """Create a fail respond with detail=message."""
        self.status = RtnStatus.FAIL
        self.detail = message
        return self.to_json()

    def warning(self, message: str | dict):
        """Create a warning respond with detail=message."""
        self.status = RtnStatus.WARNING
        self.detail = message
        return self.to_json()

    def success(self, message: str | dict):
        """Create a success respond with detail=message."""
        self.status = RtnStatus.SUCCESS
        self.detail = message
        return self.to_json()

    def to_dict(self) -> Dict[str, str | dict]:
        return {
            "stage": self.stage,
            "status": self.status.value,
            "detail": self.detail,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
