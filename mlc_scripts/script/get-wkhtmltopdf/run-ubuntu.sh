#!/bin/bash
wget -nc https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.jammy_amd64.deb
test $? -eq 0 || exit $?
${MLC_SUDO} dpkg -i wkhtmltox_0.12.6.1-2.jammy_amd64.deb
${MLC_SUDO} DEBIAN_FRONTEND=noninteractive apt-get install -f -y
test $? -eq 0 || exit $?

