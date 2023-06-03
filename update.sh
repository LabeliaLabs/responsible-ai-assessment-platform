#!/usr/bin/env bash

sudo apt update && \
        sudo apt upgrade && \
        sudo apt autoremove --purge && \
        sudo apt autoclean
