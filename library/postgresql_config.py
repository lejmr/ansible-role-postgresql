#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: my_sample_module

short_description: This is my sample module

version_added: "2.4"

description:
    - "This is my longer description explaining my sample module"

options:
    name:
        description:
            - This is the message to send to the sample module
        required: true
    new:
        description:
            - Control to demo if the result of this module is changed or not
        required: false

extends_documentation_fragment:
    - azure

author:
    - Your Name (@yourhandle)
'''

EXAMPLES = '''
# Pass in a message
- name: Test with a message
  my_new_test_module:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_new_test_module:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_new_test_module:
    name: fail me
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
    returned: always
message:
    description: The output message that the sample module generates
    type: str
    returned: always
'''


from ansible.module_utils.basic import AnsibleModule
import re


def get_index(fl, option):
    # Search for uncommented
    i = 0
    reoption = re.compile('^\s*{}\s*=.+$'.format(option))
    for line in fl:
        mo = reoption.search(line)
        if mo:
            return i
        i += 1

    # Search for first commented line
    i = 0
    reoption = re.compile('^\s*#\s*{}\s*=.+$'.format(option))
    for line in fl:
        mo = reoption.search(line)
        if mo:
            return i
        i += 1

    # Was not found, so placing at the end of file
    return len(fl) + 1


def is_number(val):
    try:
        float(val)
    except ValueError:
        return False
    return True


def update_value(line, value):
    changed = False
    # Clean key and value of configuration file
    ie = line.index('=')
    left, right = line[:ie], line[ie+1:]

    # key update
    key = left.strip() if left.strip()[0] != '#' else left.strip()[1:].strip()

    # value update
    comment = None
    old_value = right.strip()
    if '#' in right:
        ih = right.index('#')
        old_value = right[:ih].strip()
        comment = right[1+ih:].strip()

    # Determine if value has changed
    if is_number(old_value) and is_number(value):
        changed = True if abs(float(old_value) - float(value)) > 0.001 else False
    else:
        changed = str(old_value if old_value[0] != "'" else old_value[1:-1]).strip() != str(value).strip()

    # Format new value
    if not is_number(value):
        value = "'{}'".format(str(value))

    # Return value
    if comment:
        return changed, '{} = {}   # {}'.format(key, value, comment)
    return changed, '{} = {}'.format(key, value)


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        path=dict(type='str', required=True),
        option=dict(type='str', required=True),
        value=dict(type='str', required=True)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    with open(module.params["path"], "r") as f:
        fl = [x.rstrip() for x in f.readlines()]

    # Determine line number which is going to be changed
    ln = get_index(fl, module.params["option"])

    # Generate updated line for configuration
    if len(fl) < ln:
        new_line = '{option} = {value}'.format(**module.params)
        result["changed"] = True
        fl.append(new_line)
    else:
        result["changed"], new_line = update_value(fl[ln], module.params["value"])
        fl[ln] = new_line


    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)


    # Write changes to configuration file
    if result["changed"]:
        with open(module.params["path"], "w") as f:
            f.write("\n".join(fl))


    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result
    # if module.params['name'] == 'fail me':
    #     module.fail_json(msg='You requested this to fail', **result)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
