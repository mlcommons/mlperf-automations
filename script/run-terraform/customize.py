from mlc import utils
import os
import shutil
import json


def preprocess(i):

    os_info = i['os_info']
    env = i['env']
    logger = i['automation'].logger
    script_dir = i['run_script_input']['path']
    config_dir = os.path.join(
        script_dir, env.get(
            'MLC_TERRAFORM_CONFIG_DIR_NAME', ''))
    env['MLC_TERRAFORM_CONFIG_DIR'] = config_dir
    cache_dir = os.getcwd()

    logger.info(f"Running terraform from {cache_dir}")

    shutil.copy(os.path.join(config_dir, "main.tf"), cache_dir)
    env['MLC_TERRAFORM_RUN_DIR'] = cache_dir

    return {'return': 0}


def postprocess(i):
    logger = i["automation"].logger
    env = i['env']
    if env.get('MLC_DESTROY_TERRAFORM'):
        return {'return': 0}
    state = i['state']
    with open("terraform.tfstate") as f:
        tfstate = json.load(f)
#    print(tfstate)
    resources = tfstate['resources']
    for resource in resources:
        if resource['type'] == 'aws_instance':
            aws_resource = resource
            break
    instances_state = aws_resource['instances']
    state['MLC_TF_NEW_INSTANCES_STATE'] = []
    ssh_key_file = env.get('MLC_SSH_KEY_FILE')
    user = 'ubuntu'
    for instance_state in instances_state:
        instance_attributes = instance_state['attributes']
        state['MLC_TF_NEW_INSTANCES_STATE'].append(instance_attributes)
        public_ip = instance_attributes['public_ip']
        if env.get('MLC_TERRAFORM_MLC_INIT'):
            run_input = {
                'automation': 'script',
                'action': 'run',
                'tags': 'remote,run,ssh',
                'env': {
                },
                'host': public_ip,
                'user': user,
                'skip_host_verify': True,
                'ssh_key_file': ssh_key_file,
                'quiet': True,
                'silent': True,
                'run_cmds': [
                    "sudo apt-get update",
                    "sudo apt-get -y upgrade",
                    "sudo apt-get install -y python3-pip",
                    "python3 -m pip install mlc",
                    "source ~/.profile"
                ]
            }
            if env.get('MLC_TERRAFORM_RUN_COMMANDS'):
                run_cmds = env.get('MLC_TERRAFORM_RUN_COMMANDS')
                for cmd in run_cmds:
                    cmd = cmd.replace(":", "=")
                    cmd = cmd.replace(";;", ",")
                    run_input['run_cmds'].append(cmd)
            mlc = i['automation'].action_object
            r = mlc.access(run_input)
            if r['return'] > 0:
                return r
            # print(r)
        print_attr(instance_attributes, "id")
        print_attr(instance_attributes, "instance_type")
        print_attr(instance_attributes, "public_ip")
        print_attr(instance_attributes, "public_dns")
        print_attr(instance_attributes, "security_groups")

    return {'return': 0}


