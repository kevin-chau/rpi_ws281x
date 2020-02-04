#!/bin/bash

cd rpi_ws281x/python
sudo PYTHONPATH=".:build/lib.linux-armv7l-2.7" python examples/strandtest.py
