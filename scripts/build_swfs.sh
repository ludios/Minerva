#!/bin/sh -e
# Rebuild FlashConnector.swf (needs Haxe), then run
# scripts/build_autocachebreakers.py.
cd "$(dirname "$0")/.."

haxe -cp hx -v -swf-version 9 -swf \
./src/minerva/compiled_client/FlashConnector.swf \
-main cw.net.FlashConnector \
> ./src/minerva/compiled_client/FlashConnector.swf.log
