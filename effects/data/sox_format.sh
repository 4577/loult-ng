#!/usr/bin/env bash
# formats any soundfile to the format required by pysndfx
sox "$1" -c 1 -r 16000 -e floating-point "$2"
