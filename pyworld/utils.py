from enum import Enum
import json
from typing import Dict


class RtnStatus(Enum):
    SUCCESS = "Success"
    FAIL = "Fail"
    NOT_SET = "<Not_set>"


class ReturnResult:
    """Easy way to create function calling return response."""

    status: RtnStatus = RtnStatus.NOT_SET
    detail: dict | str = "Nothing to say here."

    def fail(self, message: str | dict):
        """Create a fail responde with detail=message."""
        self.status = RtnStatus.FAIL
        self.detail = message
        return self.to_json()

    def success(self, message: str | dict):
        """Create a success responde with detail=message."""
        self.status = RtnStatus.SUCCESS
        self.detail = message
        return self.to_json()

    def to_dict(self) -> Dict[str, str | dict]:
        return {"status": self.status.value, "detail": self.detail}

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
