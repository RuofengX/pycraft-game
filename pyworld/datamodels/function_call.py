from __future__ import annotations

import base64
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Optional

# from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

if TYPE_CHECKING:
    from pyworld.entity import Entity

Detail = Dict[str, Any] | str


class ExceptionModel(BaseModel):
    exception_name: str = ""
    exception_detail: Detail | str = ""

    @staticmethod
    def from_exception(e: Exception | None) -> Optional[ExceptionModel]:
        if e is None:
            return None
        return ExceptionModel(
            exception_name=e.__class__.__name__,
            exception_detail=str(e),
        )


class CallRequestModel(BaseModel):
    func_name: str
    kwargs: Dict[str, Any]


class CallStatus(Enum):
    NOT_SET = "<Not_set>"
    FAIL = "Fail"
    WARNING = "Warning"
    SUCCESS = "Success"


class CallResultModel(BaseModel):
    """
    Easy way to create function safe call result return.

    stage: the name or info of the calling method. Readable.
           Will auto generate by class name if not set.
    status: the result status, success or fail. Only key to do match.
    detail: the return or error message, should be readable dict | str. Readable.

    """

    stage: str = "UNKNOWN"
    status: CallStatus = CallStatus.NOT_SET
    detail: Detail = ""
    exception: Optional[ExceptionModel] = None

    def fail(self, detail: Detail, e: Optional[Exception] = None) -> str:
        """Create a fatal respond with detail=message."""
        self.status = CallStatus.FAIL
        self.detail = detail
        self.exception = ExceptionModel.from_exception(e)
        return self.to_json()

    def warning(self, message: Detail, e: Optional[Exception] = None) -> str:
        """Create a warning respond with detail=message."""
        self.status = CallStatus.WARNING
        self.detail = message
        self.exception = ExceptionModel.from_exception(e)
        return self.to_json()

    def success(self, message: str | Detail) -> str:
        """Create a success respond with detail=message."""
        self.status = CallStatus.SUCCESS
        self.detail = message
        return self.to_json()

    def to_dict(self) -> Dict[str, str | Detail]:
        return self.dict()

    def to_json(self) -> str:
        return self.json()


class ServerReturnModel(CallResultModel):
    """
    Easy way to create json response.

    Extend some useful fail states.
    """

    stage: str = "Server"

    def entity(self, entity: Entity) -> str:
        """
        Create a success respond
        with detail={'dict':..., 'obj_pickle':...}.
        """

        obj_pickle_base64 = base64.b64encode(entity.get_state_b())
        self.status = CallStatus.SUCCESS
        self.detail = {
            "dict": entity.get_state(),
            "obj_pickle_base64": str(obj_pickle_base64, encoding="utf-8"),
        }
        return self.to_json()

    def name_not_valid(self) -> str:
        return self.fail("Username not registered yet.")

    def name_already_used(self) -> str:
        return self.fail("Username already used.")

    def passwd_check_fail(self) -> str:
        return self.fail("Password check not pass.")

    # def to_json(self) -> str:
    #     """
    #     Use fastapi jsonable encoder to
    #     override the default json.dumps
    #     """

    #     return jsonable_encoder(self.to_dict())
