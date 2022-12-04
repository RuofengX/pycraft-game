from __future__ import annotations

import pickle
import random
from typing import Any, Dict
from warnings import warn

from pyworld.basic import Vector
from pyworld.player import Player
from pyworld.world import Continuum, World


class Core:
    def __init__(self, save_file_path: str | None = None) -> None:

        world = None
        if save_file_path is not None:
            try:
                with open(save_file_path, mode='rb') as f:
                    world: Any = pickle.load(f)
                    assert isinstance(world, World)
            except AssertionError:
                warn('Pickled object is not World type.')
            except pickle.UnpicklingError:
                warn('Save file is invalid.')
            except FileNotFoundError:
                warn('Save file path is not exist. Create one.')
                with open(save_file_path, mode='wb') as f:
                    f.close()
        else:
            # Set new file path.
            rnd_id: int = random.randint(100000, 999999)
            save_file_path = "./save-{0}.bin".format(rnd_id)
            print("Auto generate new save file: {}".format(save_file_path))

        self.ct: Continuum = Continuum(world=world)
        self.save_file_path: str = save_file_path

    def start(self) -> None:
        self.ct.start()

    def stop(self, save: bool = True) -> None:
        self.ct.stop()
        if save:
            self.save()

    def save(self) -> None:
        with open(self.save_file_path, mode="wb") as f:
            self.ct.pause()
            pickle.dump(self.ct.world, f, protocol=5)
            self.ct.resume()

    def register(self, username: str, passwd: str) -> Player:
        """
        Register a new player entity in the world,
        Use random position and username, passwd given.

        Return the player object.
        """

        p: Player = self.ct.world.world_new_entity(
            cls=Player,
            pos=Vector.random(),
            username=username,
            passwd=passwd,
            world=self.ct.world,
        )

        return p

    def check_login(self, username: str, passwd: str) -> bool:
        """Check username and passwd is valid"""

        if username not in self.ct.world.player_dict:
            return False
        else:
            return (
                self.player_dict[username].passwd == passwd
            )

    @property
    def player_dict(self) -> Dict[str, Player]:
        """Shorten the self.ct.world.player_dict."""

        return self.ct.world.player_dict
