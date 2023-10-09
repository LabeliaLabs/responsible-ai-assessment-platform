#!/usr/bin/env bash

# Check end of lines config: require CRLF on Unix and LF on Windows

sudo apt update && \
        sudo apt upgrade && \
        sudo apt autoremove --purge && \
        sudo apt autoclean
