from typing import ClassVar, List, Optional

from pyworld.modules.equipment import Equipment, EquipStatus
from pyworld.world import Positional, World


class Radar(Equipment[Positional]):
    require_module: ClassVar[type] = Positional

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.radius: float = 1
        self.interval_tick: int = 100
        self.auto_scan: bool = True
        self.scan_result: List[Positional] = []
        self.last_update: int = -1

    def set_scan_frequence(self, interval: int) -> None:
        self.interval_tick = interval

    def toggle_auto_scan(self, target: Optional[bool] = None) -> None:
        """Toggle radio auto_scan
        If target: bool is given, set auto_scan to target status
        """

        if target is None:
            self.auto_scan = not self.auto_scan
        else:
            self.auto_scan = target

    def _radar_tick(self, belong: World) -> None:
        if self.status != EquipStatus.OK:
            return

        assert self.owner is not None
        o = self.owner
        w = belong

        if self.auto_scan:
            if o.age % self.interval_tick == 0:  # use the interval
                self.scan_result = w.world_get_nearby_entity(
                    o, radius=self.radius
                )
                self.last_update = w.age
