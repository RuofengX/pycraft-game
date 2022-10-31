from __future__ import annotations
import pickle
import random
from typing import Optional

from pyworld.world import World, Continuum
from pyworld.player import Player
from pyworld.basic import Vector


class Core:
    def __init__(self, save_file_path: Optional[str] = None):

        world = None
        if save_file_path:
            try:
                with open(save_file_path, mode='rb') as f:
                    world = pickle.load(f)
                    assert isinstance(world, World)
            except AssertionError:
                print('Pickled object is not World type.')
            except pickle.UnpicklingError:
                print('Save file is invalid.')
            except FileNotFoundError:
                print('Save file path is not exist.')
        else:
            # Set new file path.
            rnd_id = random.randint(100000, 999999)
            save_file_path = "./save-{0}.bin".format(rnd_id)
            print("Auto generate new save file: {}".format(save_file_path))

        self.ct = Continuum(world=world)
        self.save_file_path: str = save_file_path

    def start(self):
        if self.ct.is_alive():
            self.ct.start()

    def stop(self):
        self.ct.stop()
        self.save()

    def save(self):
        with open(self.save_file_path, mode="wb") as f:
            self.ct.pause()
            pickle.dump(self.ct.world, f, protocol=5)
            self.ct.resume()

    def register(self, username: str, passwd_with_salt: str) -> Player:
        """Register a new player entity in the world,
        Use random position and username, passwd given.

        Return the player object.
        """
        p = self.ct.world.world_new_entity(
            cls=Player,
            pos=Vector.random(),
            username=username,
            passwd_with_salt=passwd_with_salt,
        )

        self.ct.world.player_dict[username] = p
        return p

    def check_login(self, username: str, passwd_with_salt: str) -> bool:
        """Check username and passwd is valid"""
        if username not in self.ct.world.player_dict.keys():
            return False
        else:
            return (
                self.player_dict[username].passwd_with_salt == passwd_with_salt
            )

    @property
    def player_dict(self):
        """Shorten the self.ct.world.player_dict."""
        return self.ct.world.player_dict
