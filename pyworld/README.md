# pyworld - a 3D sandbox with full extention

## Entity, the space

Entity is the basic thing in pyworld. It includes: simulated universe, running continuum, and everything in those world.

Continuum is the world it self. It represents a universe with space and time. It contains (a lot of) characters. It runs a tick-loop after Continuum.start() method is called.
Continuum inherits World entity, which only contains characters but no tick-loop. Actually Continuum and World is the same thing. A continuum instance is a world with time.

Character is a special kind of entity. It represents all the entity in a world. Every character has a position, velocity and acceleration.
Entity has tick() method, which will be called in every tick-loop.
Character could only be created by a Continuum in fact, 

New type of Character could be created and should herit the Character class. 
Also an entity could gain different capacity by herit multiple MixinModule.

For more MixinModule usage please refers to the docs of `./beings.py` .

## Ticks, the time

Time runs in a tick-loop in pyworld. Continuum maintains the tick-loop. Continuum instance is also a Threading instance, so there could be multi-verse technically.

When a tick happens, firstly the Continuum would call tick() method of every entity of `continuum_instance.entity_dict`.
Then the `entity_instance.tick()` method would call every method named after '_tick' of itself.

