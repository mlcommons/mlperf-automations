# Run Ansible Playbook

This MLC script runs Ansible playbooks for configuration management and remote automation.

## Usage

```bash
# Run a playbook against an inventory
mlcr run,ansible --playbook=path/to/playbook.yml --inventory=path/to/inventory.ini

# Run with extra variables
mlcr run,ansible --playbook=setup.yml --inventory=hosts.ini --extra_vars="key1=value1 key2=value2"

# Run with sudo (become)
mlcr run,ansible --playbook=setup.yml --inventory=hosts.ini --become=yes

# Run with specific tags
mlcr run,ansible --playbook=setup.yml --inventory=hosts.ini --tags=install,configure

# Run with increased verbosity
mlcr run,ansible --playbook=setup.yml --inventory=hosts.ini --verbosity=vvv

# Run with a specific SSH key
mlcr run,ansible --playbook=setup.yml --inventory=hosts.ini --private_key=~/.ssh/my_key --user=ubuntu

# Run with vault password file
mlcr run,ansible --playbook=setup.yml --inventory=hosts.ini --vault_password_file=~/.vault_pass

# Install galaxy requirements before running
mlcr run,ansible --playbook=setup.yml --inventory=hosts.ini --galaxy_requirements=requirements.yml

# Limit to specific hosts
mlcr run,ansible --playbook=setup.yml --inventory=hosts.ini --limit=host1,host2
```

## Input Options

| Option | Description |
|--------|-------------|
| `--playbook` | Path to the Ansible playbook YAML file (required) |
| `--inventory` | Path to the inventory file |
| `--extra_vars` | Extra variables to pass to the playbook |
| `--limit` | Limit execution to specific hosts |
| `--tags` | Only run tasks with these tags |
| `--skip_tags` | Skip tasks with these tags |
| `--forks` | Number of parallel processes (default: 5) |
| `--verbosity` | Verbosity level: v, vv, vvv, or vvvv |
| `--private_key` | Path to SSH private key |
| `--user` | Remote SSH user |
| `--become` | Run with sudo/become |
| `--vault_password_file` | Path to vault password file |
| `--config_file` | Path to ansible.cfg |
| `--roles_path` | Path to additional roles |
| `--galaxy_requirements` | Path to Galaxy requirements.yml to auto-install |

## Examples

See the `examples/` directory for sample playbooks and inventory files.
