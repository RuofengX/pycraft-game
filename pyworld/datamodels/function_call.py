from __future__ import annotations

import base64
import json
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Optional, Self, overload

# from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from pyworld.basic import Jsonable
from pyworld.datamodels.status_code import CallStatus


if TYPE_CHECKING:
    from pyworld.entity import Entity

Detail = Dict[str, Any] | str


class IntelliDump(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if hasattr(o, '__getstate__'):
            return o.__getstate__()
        else:
            return super().default(o)


class ExceptionModel(BaseModel):
    exception_name: str = ""
    exception_detail: Detail | str = ""

    @overload
    @staticmethod
    def from_exception(e: None) -> None:
        ...

    @overload
    @staticmethod
    def from_exception(e: Exception) -> ExceptionModel:
        ...

    @staticmethod
    def from_exception(e: Optional[Exception]) -> Optional[ExceptionModel]:
        if e is None:
            return None
        return ExceptionModel(
            exception_name=e.__class__.__name__,
            exception_detail=str(e),
        )


class CallRequestModel(BaseModel):
    func_name: str
    kwargs: Dict[str, Any]


class CallResultModel(BaseModel):
    """
    Easy way to create function safe call result return.

    stage: the name or info of the calling method. Readable.
           Will auto generate by class name if not set.
    status: the result status, success or fail. Only key to do match.
    detail: the return or error message, should be readable dict | str. Readable.

    """

    stage: str = "UNKNOWN"
    status: CallStatus = CallStatus.INIT
    detail: Detail = ""
    exception: Optional[ExceptionModel] = None

    class Config:
        json_encoders = {
            Enum: lambda e: e.value,
            Jsonable: IntelliDump().default,
        }

    def fail(self, detail: Detail, e: Optional[Exception] = None) -> Self:
        """Create a fatal respond with detail=message."""
        self.status = CallStatus.FAIL
        self.detail = detail
        self.exception = ExceptionModel.from_exception(e)
        return self

    def warning(self, message: Detail, e: Optional[Exception] = None) -> Self:
        """Create a warning respond with detail=message."""
        self.status = CallStatus.WARNING
        self.detail = message
        self.exception = ExceptionModel.from_exception(e)
        return self

    def success(self, message: Detail) -> Self:
        """Create a success respond with detail=message."""
        self.status = CallStatus.SUCCESS
        self.detail = message
        return self

    def to_dict(self) -> Dict[str, str | Detail]:
        return self.dict()

    def to_json(self) -> str:
        return self.json()


class ServerResultModel(CallResultModel):
    """
    Easy way to create json response.

    Extend some useful fail states.
    """

    stage: str = "Server"

    def entity(self, entity: Entity) -> Self:
        """
        Create a success respond
        with detail={'dict':..., 'obj_pickle':...}.
        """

        obj_pickle_base64 = base64.b64encode(entity.get_state_b())
        detail = {
            "dict": entity.get_state(),
            "obj_pickle_base64": str(obj_pickle_base64, encoding="utf-8"),
        }
        return self.success(detail)

    def name_not_valid(self) -> Self:
        return self.fail("Username not registered yet.")

    def name_already_used(self) -> Self:
        return self.fail("Username already used.")

    def passwd_check_fail(self) -> Self:
        return self.fail("Password check not pass.")
