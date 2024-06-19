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
Look at How To for examples of common operations.
Also look at `.client.RoboMasterClient` for a list of available methods on the robot.

.. include:: ../../md_docs/how_to.md

.. include:: ../../md_docs/faq.md
"""

from .client import *
from .data import *
from .dropping_feed import *
from .feed import *