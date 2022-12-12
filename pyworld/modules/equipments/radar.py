from dataclasses import dataclass, field
from typing import ClassVar, List, Optional, Type, cast

from pyworld.entity import Entity
from pyworld.modules.equipment import Equipment, EquipmentMixin, EquipmentStatus
from pyworld.world import Character, World


@dataclass
class Radar(Equipment):
    required_module: ClassVar[List[Type[Entity]]] = [Character]
    radius: int = 0
    interval_tick: int = 100
    auto_scan: bool = True
    scan_result: List[Character] = field(default_factory=list)
    last_update: int = -1

    def set_scan_tick(self, interval: int):
        self.interval_tick = interval

    def toggle_auto_scan(self, target: Optional[bool] = None):
        """Toggle radio auto_scan
        If target: bool is given, set auto_scan to target status
        """
        if target is None:
            self.auto_scan = not self.auto_scan
        else:
            self.auto_scan = target

    def _tick(self, o: EquipmentMixin, w: World):
        if self.status == EquipmentStatus.FINE:  # o is
            if self.auto_scan:
                if o.age % self.interval_tick == 0:  # use the interval
                    self.characters_list = w.world_get_nearby_entity(
                        char=o, radius=self.radius
                    )
                    self.last_update = w.age
