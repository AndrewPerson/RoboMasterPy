"""
# SBHS RoboMaster API
A Python library for controlling the RoboMaster EP Core robot.

## Installation
```sh
pip install sbhs-robomaster
```

## Pre-requisite knowledge
This library heavily relies on async code and async iterators.

A good tutorial on async code is at [https://superfastpython.com/python-asyncio/](https://superfastpython.com/python-asyncio/)
and the documentation is at [https://docs.python.org/3/library/asyncio.html](https://docs.python.org/3/library/asyncio.html).

No knowledge about iterators or async iterators is needed as the usage is very simple. But a good tutorial on iterators is at
[https://www.pythonlikeyoumeanit.com/Module2_EssentialsOfPython/Iterables.html](https://www.pythonlikeyoumeanit.com/Module2_EssentialsOfPython/Iterables.html)
and one on async iterators at [https://superfastpython.com/python-asyncio/#Asynchronous_Iterators](https://superfastpython.com/python-asyncio/#Asynchronous_Iterators).

## Usage
```py
import asyncio
from sbhs_robomaster import connect_to_robomaster, DIRECT_CONNECT_IP

async def main():
    async with await connect_to_robomaster(DIRECT_CONNECT_IP) as robot:
        await robot.move(0.5, 0.5, 0) # Move forward by 0.5m and to the right by 0.5m

        await robot.move(0, 0, 90) # Rotate clockwise by 90 degrees

        # Do other stuff
```

Look at `.client.RoboMasterClient` for a list of available methods on the robot.
Also look at How To for more examples.

.. include:: ../../md_docs/how_to.md

.. include:: ../../md_docs/faq.md
"""

from .client import *
from .data import *
from .dropping_async_enumerable import *
from .feed import *