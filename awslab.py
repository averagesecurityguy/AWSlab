#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013, LCI Technology Group
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#  Redistributions of source code must retain the above copyright notice, this
#  list of conditions and the following disclaimer.
#
#  Redistributions in binary form must reproduce the above copyright notice,
#  this list of conditions and the following disclaimer in the documentation
#  and/or other materials provided with the distribution.
#
#  Neither the name of LCI Technology Group nor the names of its contributors
#  may be used to endorse or promote products derived from this software
#  without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
import sys
import json
import logging
import boto.ec2

import aws.securitygroup
import aws.instance
import aws.keypair

#-----------------------------------------------------------------------------
# Function definitions
#-----------------------------------------------------------------------------
def info(msg):
    logging.info(msg)
    print msg


def get_aws_connection():
    '''Get a connection to an AWS region.'''
    try:
        return boto.ec2.connect_to_region(bconfig['aws_region'],
                                aws_access_key_id=bconfig['aws_key'],
                                aws_secret_access_key=bconfig['aws_secret'])
    except boto.exception.EC2ResponseError as e:
        logging.critical(e.message)
        raise 'Unable to make connection to AWS.'


def bootstrap():
    '''
    Prepare an AWS region for the lab machines by creating the security
    group and SSH keypair if they do not exist.
    '''
    info('Bootstrapping region {0}'.format(bconfig['aws_region']))
    sg = aws.securitygroup.SecurityGroup(bconfig['security_group'], conn)
    info('Security group "{0}" is ready.'.format(sg.name))
    kp = aws.keypair.KeyPair(bconfig['key_pair'], bconfig['ssh_path'], conn)
    info('Key pair "{0}" is ready.'.format(kp.name))

def start():
    '''
    Create a new instance, start an existing one that is stopped, or attach
    to a running instance. Add any needed rules to the security group and
    run the commands specified in the configuration file.
    '''
    id = iconfig.get('id')
    if id is None:
        info('Creating new instance.')
    else:
        info('starting instance {0}.'.format(id))

    sg = aws.securitygroup.SecurityGroup(bconfig['security_group'], conn)
    kp = aws.keypair.KeyPair(bconfig['key_pair'], bconfig['ssh_path'], conn)
    i = aws.instance.AWSInstance(iconfig, kp.name, kp.pem, sg.name, conn)
    if i.status != 'running':
        i.start()

    info('Instance is running, the public DNS name is {0}.'.format(i.public_dns))

    # Add the instance id and public DNS name to the configuration and save it.
    iconfig['id'] = i.id
    iconfig['public_dns'] = i.public_dns
    save_config(iconfig_file, iconfig) 
    
    rules = iconfig.get('rules', [])
    info('Adding {0} rules to the security group.'.format(len(rules)))
    sg.add_rules(rules)

    info('Waiting until instance is ready to receive commands.')
    i.connect_ssh(kp.pem)

    # Only run commands on first run. Allows for stopping and restarting the
    # machine.
    if iconfig.get('first_run', True) is True:
        iconfig['first_run'] = False
        save_config(iconfig_file, iconfig)
        commands = iconfig.get('commands', [])
        info('Running {0} commands.'.format(len(commands)))
        i.run_commands(commands)
    else:
        info('The "first_run" key is set to false, no commands executed.')


def stop():
    '''
    Stop the instance specified by the instance_id. If the instance_id is
    None, then log an error and quit.
    '''
    id = iconfig.get('id')
    if id is not None:
        info('Stopping instance {0}.'.format(id))
        sg = aws.securitygroup.SecurityGroup(bconfig['security_group'], conn)
        kp = aws.keypair.KeyPair(bconfig['key_pair'], bconfig['ssh_path'], conn)
        i = aws.instance.AWSInstance(iconfig, kp.name, kp.pem, sg.name, conn)

        # Remove the public DNS name from the configuration and save it.
        iconfig.pop('public_dns')
        save_config(iconfig_file, iconfig)
        
        i.stop()
    else:
        logging.critical('Invalid instance id: {0}.'.format(id))


def terminate():
    '''
    Terminate the instance specified by the instance_id. If the instance_id is
    None, then log an error and quit.
    '''
    id = iconfig.get('id')
    if id is not None:
        print 'Terminating instance {0}.'.format(id)
        sg = aws.securitygroup.SecurityGroup(bconfig['security_group'], conn)
        kp = aws.keypair.KeyPair(bconfig['key_pair'], bconfig['ssh_path'], conn)
        i = aws.instance.AWSInstance(iconfig, kp.name, kp.pem, sg.name, conn)

        # Remove the instance id and public_dns from the configuration data
        # and set first run back to true. Finally, update the configuration
        # file.
        iconfig['first_run'] = True
        iconfig.pop('id')
        iconfig.pop('public_dns')
        save_config(iconfig_file, iconfig)

        i.terminate()
    else:
        logging.critical('Invalid instance id: {0}'.format(id))


def load_config(config_file):
    '''Load the configuration data from a JSON file.'''
    try:
        return json.loads(open(config_file).read())
    except Exception as e:
        print 'Error loading config file: {0}.'.format(e)
        sys.exit(1)


def save_config(config_file, config):
    '''Save configuration data to a file in JSON format.'''
    config_file = open(config_file, 'w')
    config_file.write(json.dumps(config, indent=2))
    config_file.close()


#-----------------------------------------------------------------------------
# Main program
#-----------------------------------------------------------------------------
# Setup global variables
bconfig = load_config('configs/bootstrap.cfg')
iconfig = None
iconfig_file = None
command = None

# Configure logging
logging.basicConfig(level=logging.ERROR)
logging.getLogger('boto').setLevel(logging.CRITICAL)

# Parse command line arguments
if len(sys.argv) == 2:
    command = sys.argv[1]
elif len(sys.argv) == 3:
    command = sys.argv[1]
    iconfig_file = sys.argv[2]
    iconfig = load_config(iconfig_file)
else:
    print 'USAGE: aws_lab command <config_file>'
    sys.exit()

# Make sure we have a config file if we need it.
config_commands = ['start', 'stop', 'terminate']
if (command in config_commands) and (iconfig is None):
    print 'This command requires a configuration file.'
    sys.exit(1)

# Create a new AWS connection
conn = get_aws_connection()

# Execute the specified command
if command == 'bootstrap':
    bootstrap()
elif command == 'start':
    start()
elif command == 'stop':
    stop()
elif command == 'terminate':
    terminate()
else:
    print '\n{0}\n'.format(open('README').read())
