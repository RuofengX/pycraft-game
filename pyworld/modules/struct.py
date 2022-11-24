from __future__ import annotations
from typing import NamedTuple
from threading import Lock

from pyworld.world import Character, World


class Structure(NamedTuple):
    shield: float = 0
    armor: float = 0
    backup: float = 0

    def __sub__(self, other: Structure):
        l_other = list(other)
        return Structure(
            self.shield - l_other[0],
            self.armor - l_other[1],
            self.backup - l_other[2],
        )


class BodyMixin(Character):
    """Define a character that could be destroyed."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.body_completeness: float = 100
        self.is_destroyed: bool = False

    def _destroy(self) -> None:
        self.is_destroyed = True

    def _body_tick(self, belong: World):
        if self.body_completeness <= 0:
            self._destroy()


class StructMixin(BodyMixin):
    """StructMixin, with HP and more."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.structure = Structure(0, 0, 100)

    def __static_init__(self):
        super().__static_init__()
        self.__structure_lock = Lock()

    def _struct_get_damage(self, loss: Structure):
        with self.__structure_lock:
            self.structure -= loss
