from __future__ import annotations

from typing import Any, Callable, Dict

from pyworld.datamodels.function_call import RequestModel, ResultModel
from pyworld.entity import Entity


class ControlResultModel(ResultModel):
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
                        docs = str(docs)
                        docs = docs.strip()
                        rtn[func_name] = docs
        return rtn

    def ctrl_list_property(self) -> Dict[str, Any]:
        """
        Return a properties list
        name as the key, value as the values.
        """

        rtn: Dict[str, Any] = {}
        with self._tick_lock:
            for property_name in dir(self):
                if property_name[0] != "_":  # Ignore attr start with _
                    pty: Any = getattr(self, property_name)
                    if not callable(pty):
                        rtn[property_name] = str(pty)
            return rtn

    def ctrl_safe_call(self, data: RequestModel) -> ControlResultModel:
        """
        Call a func list in self.ctrl_list().
        func_name is the target method's name,
        use **kwargs attachment as the arguments.
        """

        rtn = ControlResultModel(stage='ctrl_safe_call')

        result: str = ''

        try:
            if data.func_name in self.ctrl_list_method():
                method: Callable[..., Any] = getattr(self, data.func_name)
                result = str(method(**data.kwargs))
                rtn.success(message=str(result))
        except Exception as e:
            rtn.fail(detail=str(result), e=e)
        finally:
            return rtn
