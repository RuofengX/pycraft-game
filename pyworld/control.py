from __future__ import annotations
from typing import Dict, Any, Callable
from functools import cache, cached_property

from pprint import pprint as print

from pyworld.entity import Entity
from pyworld.utils import Result


class ControlResult(Result):
    pass


class ControlMixin(Entity):
    """
    A magic mixin that provide a control protocol,
    To make the class as controllable.

    It will expose all mixins' methods, use _ to mask inner method.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @cached_property
    def _ctrl_dir_cache(self) -> list:
        return dir(self)

    def ctrl_refresh_cache(self) -> None:
        """
        Clear all ctrl property cache.
        Useful when the instance's attribute is changed.
        """

        for c in [
                self.ctrl_list_method,
        ]:
            c.cache_clear()

    @cache
    def ctrl_list_method(self) -> Dict[str, str]:
        """
        Return a functions dict
        name as the key, __docs__ as the values.
        """

        rtn = {}
        with self._tick_lock:
            for func_name in dir(self):
                if func_name[0] != '_':  # Ignore attr start with _
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

        rtn = {}
        with self._tick_lock:
            for property_name in dir(self):
                if property_name[0] != '_':  # Ignore attr start with _
                    pty = getattr(self, property_name)
                    if not callable(pty):
                        rtn[property_name] = str(pty)
            return rtn

    def ctrl_safe_call(self, func_name: str, **kwargs) -> ControlResult:
        """
        Call a func list in self.ctrl_list().
        func_name is the target method's name,
        use **kwargs attachment as the arguments.
        """
        # TODO: make it asyncable and run in next tick.

        rtn = ControlResult()

        self.ctrl_refresh_cache()  # Refresh the cache.

        try:
            if func_name in self.ctrl_list_method():
                mtd: Callable = getattr(self, func_name)
                result: Any = mtd(**kwargs)
                rtn.success(message=str(result))
        except Exception as e:
            rtn.fail(str(e))
        finally:
            return rtn


if __name__ == '__main__':
    a = ControlMixin(eid=1)
    print(a.ctrl_list_method().keys())

    print('#' * 88)

    setattr(a, 'test', b'1')
    import pickle
    setattr(a, 'test_b', pickle.dumps(a))
    r = a.ctrl_list_property()
    print(r)

    def test(k):
        print(k)
    setattr(a, 'test', test)
    a.ctrl_list_method.cache_clear()
    rtn = a.ctrl_safe_call('test')
    print(rtn)
