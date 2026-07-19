MLC_PYTHON_BIN=${MLC_PYTHON_BIN_WITH_PATH:-python3}

${MLC_PYTHON_BIN} -m pip install --upgrade pip ${MLC_PYTHON_PIP_COMMON_EXTRA}
${MLC_PYTHON_BIN} -m pip install setuptools testresources wheel h5py --user --upgrade --ignore-installed ${MLC_PYTHON_PIP_COMMON_EXTRA}

curl https://sh.rustup.rs -sSf -o tmp.sh
sh tmp.sh -y 
