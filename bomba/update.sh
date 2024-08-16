#!/bin/bash

SCRIPT_PATH="${PWD}/control.py"

# Copy the .in file to a staging control-bomba.service
cp control-bomba.service.in control-bomba.service

# Replace the placeholders with actual values using sed on the staging file
sed -i "s/@USER@/$SUDO_USER/g" control-bomba.service
sed -i "s/@SCRIPT_PATH@/$SCRIPT_PATH/g" control-bomba.service

# Copy the modified staging file to the systemd directory
sudo cp control-bomba.service /etc/systemd/system/

# Check if reload is needed and reload if necessary
if sudo systemctl is-enabled --quiet control-bomba.service && \
   [[ $(systemctl show control-bomba.service -p NeedDaemonReload --value) == yes ]]; then
    echo "Reloading systemd daemon..."
    sudo systemctl daemon-reload
    echo "Restarting control-bomba service..."
    sudo systemctl restart control-bomba.service
else
    echo "Enabling and starting control-bomba service..."
    sudo systemctl enable control-bomba.service
    sudo systemctl start control-bomba.service
fi