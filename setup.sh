#!/bin/bash
if [ -f /etc/debian_version ]; then
    ./debian.setup.sh
elif [ -f /etc/redhat-release ]; then
    ./redhat.setup.sh
else
    echo "Unsupported platform"
fi
