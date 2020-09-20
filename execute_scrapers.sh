#!/usr/bin/env sh
SCRIPT=$(readlink -f "$0")
SCRIPT_PATH=$(dirname "$SCRIPT")
$SCRIPT_PATH/env/bin/python $SCRIPT_PATH/torrent_web_scraper.py
