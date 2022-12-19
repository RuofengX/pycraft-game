from dataclasses import dataclass, field
from typing import ClassVar, List, Optional, Type, get_args

from pyworld.modules.equipment import Equipment, EquipStatus
from pyworld.world import Character, Positional, World


@dataclass
class Radar(Equipment[Positional]):
    required_module: ClassVar[Type[Character]] = Character
    radius: int = 0
    interval_tick: int = 100
    auto_scan: bool = True
    scan_result: List[Character] = field(default_factory=list)
    last_update: int = -1

    def set_scan_tick(self, interval: int) -> None:
        self.interval_tick = interval

    def toggle_auto_scan(self, target: Optional[bool] = None) -> None:
        """Toggle radio auto_scan
        If target: bool is given, set auto_scan to target status
        """
        if target is None:
            self.auto_scan = not self.auto_scan
        else:
            self.auto_scan = target

    def _tick(self, o: Character, w: World) -> None:
        super()._tick(o, w)
        if self.status == EquipStatus.FINE:  # o is Character
            if self.auto_scan:
                if o.age % self.interval_tick == 0:  # use the interval
                    self.characters_list = w.world_get_nearby_entity(
                        char=o, radius=self.radius
                    )
                    self.last_update = w.age

