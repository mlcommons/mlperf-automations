#!/bin/bash
# This script installs wkhtmltopdf on Amazon Linux
curl -L -o wkhtmltox-0.12.6-1.macos-cocoa.pkg https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox-0.12.6-1.macos-cocoa.pkg
${MLC_SUDO} installer -pkg wkhtmltox-0.12.6-1.macos-cocoa.pkg -target /

wkhtmltopdf --version
test $? -eq 0 || exit $?
