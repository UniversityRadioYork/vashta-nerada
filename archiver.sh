#!/bin/bash

SCRIPT_DIR="/home/archiver/vashta-nerada"
python3 $SCRIPT_DIR/archiver.py --weaponised > /filestore/Archive/logs/"$(date '+%Y-%m-%d')".log 2>&1
