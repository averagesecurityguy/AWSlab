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

#-----------------------------------------------------------------------------
# Function Definitions
#-----------------------------------------------------------------------------
def verify_bootstrap_config(config_file):
    config = load_config(config_file)
    keys = ['aws_key', 'aws_secret', 'aws_region', 'security_group',
            'ssh_path', 'key_pair']

    for key in keys:
        if key not in config:
            print 'The "{0}" key is not in the bootstrap file.'.format(key)

 
def verify_instance_config(config_file):
    config = load_config(config_file)
    keys = ['ami', 'type', 'ssh_user', 'rules', 'commands', 'description']

    for key in keys:
        if key not in config:
            print 'The "{0}" key is not in the instance file.'.format(key)


def verify_config(file_type, config_file):
    if file_type.lower() == 'bootstrap':
        verify_bootstrap_config(config_file)
    elif file_type.lower() == 'instance':
        verify_instance_config(config_file)
    else:
        print 'Invalid file type {0}. Quitting.'.format(file_type)
        sys.exit(1)


def load_config(config_file):
    '''Load the configuration data from a JSON file.'''
    try:
        return json.loads(open(config_file).read())
    except Exception as e:
        print 'Error loading config file: {0}.'.format(e)
        sys.exit(1)


#-----------------------------------------------------------------------------
# Main Program
#-----------------------------------------------------------------------------
usage = '''
Verify_config.py is used to ensure the required configuration data is present
in the specified configuration file. Specify a file_type of bootstrap or
instance, then specify the configuration file. If there are no errors with the
configuration file then there will be no output.

USAGE: verify_config.py file_type config_file

'''
if len(sys.argv) == 3:
    verify_config(sys.argv[1], sys.argv[2])
else:
    print usage
