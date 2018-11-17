#!/bin/bash

echo "Installing required packages."
os_packages="python3-pip"
py_packages="aiohttp"

sudo apt-get update

for package in $os_packages
do
    if dpkg -l $package; then
        echo "$package alread installed."
    else
        echo "$package not install"
        echo "Installing $package..."
       sudo apt -y install $package
    fi
done

for module in $py_packages
do
    if /usr/bin/python3 -c "import $module" > /dev/null; then
        echo "$module already installed."
    else
        echo "$module not installed"
        echo "Installing $module..."
        sudo pip3 install $module
    fi
done

echo "Done installing all packages"

echo "Installing WebSnap"
if [ -d /opt/websnap ]; then
    echo "'websnap' source already present in /opt. Please remove/rename existing source from /opt and run 'install.sh' again"
    exit 1
else
    sudo cp -r ../../websnap /opt
    sudo chown -R $USER:$USER /opt/websnap
    echo "Websnap installed to /opt"
fi

RELEASE_VERSION=$(lsb_release -sr)
if [ $RELEASE_VERSION == "16.04" ]; then
    echo "Installing websnap service"
    if [ -e /etc/systemd/system/websnap.service ]; then
        echo "Service configuration file /etc/systemd/system/websnap.service already exists."
    else
        sudo cp ./websnap.service /etc/systemd/system/websnap.service
        echo "/etc/systemd/system/websnap.service configuration file copied."
    fi

    echo "Starting WebSnap service"
    sudo systemctl enable websnap.service
    sudo systemctl restart websnap.service

else
    echo "Supported only for Ubuntu 16.04."
fi

echo "WebSnap is ready."
