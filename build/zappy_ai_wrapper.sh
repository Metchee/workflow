#!/bin/bash
export PYTHONPATH="/home/gabinrudigoz/zappy/workflow/ai/src:$PYTHONPATH"
exec "/usr/bin/python3.14" "/home/gabinrudigoz/zappy/workflow/ai/src/main.py" "$@"
