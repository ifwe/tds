#!/bin/bash

scripts=$( dirname "${BASH_SOURCE-$0}" )
source "$scripts/python-setup.sh"

time behave --junit ||:
