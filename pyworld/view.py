"""Rander the view of the entity."""
from typing import List

from pyworld.world import Character
from pyworld.basic import Vector


class ViewMixin(Character):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.view_fov: float = 1.0
        self.view_direct: Vector = Vector(1, 0, 0)
        self.view_width: int = 40
        self.view_height: int = 30
        self.view_plot: List[Vector] = []

    def view_add_entity(self, e: Character):
        pass  # TODO

    def view_update_direct(self, new: Vector):
        self.view_direct = new.unit()

    def view_get_projection(self, a: Character):
        p = self
        p_a = a.position - p.position
        print(p_a.raw_array)

        p_w_length = Vector.dotproduct(p_a, p.view_direct)
        if p_w_length == 0:
            return
        p_a1 = p_a / p_w_length
        u_a1 = p_a1 - p.view_direct
        self.view_plot.append(u_a1)


if __name__ == '__main__':
    v = ViewMixin(eid=1, pos=Vector(1, 0, 0))
    a = Character(eid=1, pos=Vector(3, 4, 0))
    v.view_get_projection(a)
    print(v.view_plot)
