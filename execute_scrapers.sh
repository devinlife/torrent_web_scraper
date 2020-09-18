#!/bin/bash
SCRIPT=$(readlink -f "$0")
SCRIPT_PATH=$(dirname "$SCRIPT")
$SCRIPT_PATH/env/bin/python torrent_web_scraper.py
