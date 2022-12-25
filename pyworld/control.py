from __future__ import annotations

import base64
import pickle
from typing import Any, Callable, Dict, NoReturn

from pyworld.datamodels.function_call import CallRequestModel, CallResultModel
from pyworld.entity import Entity


class ControlResultModel(CallResultModel):
    pass


class ControlMixin(Entity):
    """
    A magic mixin that provide a control protocol,
    To make the class as controllable.

    It will expose all mixins' methods, use _ to mask inner method.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.__cache: Dict[str, Dict[str, Any]] = {}

    def __static_init__(self) -> None:
        super().__static_init__()

    def ctrl_list_method(self) -> Dict[str, str]:
        """
        Return a functions dict
        name as the key, __docs__ as the values.
        """

        rtn: Dict[str, str] = {}
        with self._tick_lock:
            for func_name in dir(self):
                if func_name[0] != "_":  # Ignore attr start with _
                    mtd = getattr(self, func_name)
                    if callable(mtd):
                        docs = getattr(self, func_name).__doc__
                        docs = str(docs).strip()
                        rtn[func_name] = docs
        return rtn

    def ctrl_list_property(self) -> Dict[str, Any]:
        """
        Return a properties list
        name as the key, value as the values.
        """

        with self._tick_lock:
            return {k: str(v) for k, v in self.get_state().items()}

    def ctrl_get_property(self, name: str) -> str | NoReturn:
        """
        Return the value of given property
        Use base64 and pickle.

        Raise KeyError if name is invalid.
        """
        if name in self._dir_mask:
            raise KeyError(name)

        with self._tick_lock:
            return base64.b64encode(pickle.dumps(self.__getstate__()[name])).decode(
                "utf-8"
            )

    def ctrl_safe_call(self, data: CallRequestModel) -> ControlResultModel:
        """
        Call a func list in self.ctrl_list().
        func_name is the target method's name,
        use **kwargs attachment as the arguments.
        """

        rtn = ControlResultModel(stage="ctrl_safe_call")

        result: str | Dict[Any, Any] = ""

        try:
            if data.func_name in self.ctrl_list_method():
                method: Callable[..., Any] = getattr(self, data.func_name)
                result = method(**data.kwargs)
                if isinstance(result, dict):
                    rtn.success(message=result)
                else:
                    rtn.success(message=str(result))
        except Exception as e:
            rtn.fail(detail=str(result), e=e)
        finally:
            return rtn
