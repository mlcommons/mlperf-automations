#!/bin/bash
# This script installs wkhtmltopdf on Amazon Linux

# Download the wkhtmltopdf package
wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox-0.12.6-1.centos6.x86_64.rpm

# Install the package
${MLC_SUDO} yum localinstall -y wkhtmltox-0.12.6-1.centos6.x86_64.rpm --nobest --skip-broken
