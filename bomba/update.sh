#!/bin/bash

SCRIPT_PATH="${PWD}/control.py"

# Copy the .in file to a staging control-bomba.service
cp control-bomba.service.in control-bomba.service

# Replace the placeholders with actual values using sed on the staging file
sed -i "s/@USER@/$SUDO_USER/g" control-bomba.service
sed -i "s/@SCRIPT_PATH@/$SCRIPT_PATH/g" control-bomba.service

# Copy the modified staging file to the systemd directory
sudo cp control-bomba.service /etc/systemd/system/

# Reload systemd and enable the service
sudo systemctl daemon-reload
sudo systemctl enable control-bomba.service

# Start the service
sudo systemctl start control-bomba.service