from typing import Dict, List, Any

import dictdiffer  # type: ignore[import]

from pyworld.control import ControlMixin


class PropertyCache(Dict[int, Dict[str, Any]]):
    """
    Temp Memorize cache,

    Used to transfer diff data in websocket connection
    """

    def __init__(self) -> None:
        super().__init__(self)

    def get_raw(self, ent: ControlMixin) -> Dict[str, Any]:
        return ent.ctrl_list_property()

    def get_entity_property(self, ent: ControlMixin) -> Dict[str, Any]:
        rtn = self.get_raw(ent)
        self[ent.uuid] = rtn
        return rtn

    def get_diff_property(self, ent: ControlMixin) -> Dict[str, List[Any]]:
        ent_id: int = ent.uuid
        raw: Dict[str, Any] = self.get_raw(ent)
        if ent_id not in self:
            self[ent_id] = {}
        diff: List[Any] = list(dictdiffer.diff(self[ent.uuid], raw))
        self[ent.uuid] = raw
        return {"diff": diff}
