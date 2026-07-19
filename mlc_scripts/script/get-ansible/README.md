# Get Ansible

This MLC script detects or installs Ansible.

## Usage

```bash
# Detect ansible (installs if not found)
mlcr get,ansible
```

## Exported Environment

| Variable | Description |
|----------|-------------|
| `MLC_ANSIBLE_BIN_WITH_PATH` | Full path to ansible-playbook binary |
| `MLC_ANSIBLE_INSTALLED_PATH` | Directory containing ansible binaries |
| `MLC_ANSIBLE_VERSION` | Detected ansible version |
