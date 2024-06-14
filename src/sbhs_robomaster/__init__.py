"""
# SBHS RoboMaster API
A Python library for controlling the RoboMaster EP Core robot.

## Installation
```sh
pip install sbhs-robomaster
```

## Pre-requisite knowledge
This library heavily relies on async code.

A good tutorial on async code is at [https://superfastpython.com/python-asyncio/](https://superfastpython.com/python-asyncio/)
and the documentation is at [https://docs.python.org/3/library/asyncio.html](https://docs.python.org/3/library/asyncio.html).

## Usage
```py
import asyncio
from sbhs_robomaster import connect_to_robomaster, DIRECT_CONNECT_IP

async def main():
    async with await connect_to_robomaster(DIRECT_CONNECT_IP) as robot:
        await robot.set_speed(0.5, 0.5) # Move forward by 0.5m/s and to the right by 0.5m/s

        await asyncio.sleep(1) # Wait 1 second

        await robot.set_speed(0, 0) # Stop moving

        await robot.move(0, 0, 90) # Rotate clockwise by 90 degrees

        # This delay is important because due to limitations of the communication protocol,
        # the previous `move` call completes before the robot finishes turning.
        await asyncio.sleep(5) # Wait 5 seconds.

        # Do other stuff
```

Look at `.client.RoboMasterClient` for a list of available methods on the robot.
Also look at How To for more examples.

.. include:: ../../md_docs/how_to.md

.. include:: ../../md_docs/faq.md
"""

from .client import *
from .data import *
from .dropping_feed import *
from .feed import *