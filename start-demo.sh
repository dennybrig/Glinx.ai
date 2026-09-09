#!/bin/sh
set -eu
cd "$(dirname "$0")"
exec python3 -m glinx_discovery demo --serve
