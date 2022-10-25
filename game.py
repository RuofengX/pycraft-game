from dataclasses import dataclass
import pickle

from pyworld.world import Continuum


@dataclass
class Core:
    listen_ip: str = '0.0.0.0'
    listen_port: int = 2048
    ct: Continuum = Continuum()
    save_file_path: str = './save.bin'

    def __post_init__(self):
        pass

    def start(self):
        self.ct.start()

    def stop(self):
        self.ct.stop()
        self.save()

    def save(self):
        with open(self.save_file_path, mode='wb') as f:
            self.ct.pause()
            pickle.dump(self.ct.world, f, protocol=5)
            self.ct.resume()
