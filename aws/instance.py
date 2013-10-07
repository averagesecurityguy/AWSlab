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
import time
import logging
import boto.ec2
import fabric.api

class AWSInstance():
    def __init__(self, iconfig, key, pem, group, conn):
        '''
        Create or connect to an existing instance in the specified region
        region.
        '''
        self.__log = logging.getLogger('Instance')
        self.__conn = conn
        self.type = iconfig.get('type')
        self.ami = iconfig.get('ami')
        self.user = iconfig.get('ssh_user')
        self.description = iconfig.get('description')

        id = iconfig.get('id')
        self.__instance = self.__get_aws_instance(id, key, group)

    def __get_aws_instance(self, id, key, group):
        '''
        Get a list of AWS instance objects. If the instance id we want is
        not in the list, then create it.
        '''
        instances = self.__conn.get_only_instances()

        if id not in [i.id for i in instances]:
            instance = self.__create_aws_instance(key, group)
        else:
            for i in instances:
                if i.id == id:
                    instance = i

        return instance

    def __create_aws_instance(self, key_pair, security_group):
        '''Create a single instance and return the instance object.'''
        try:
            res = self.__conn.run_instances(
                    self.ami,
                    key_name=key_pair,
                    instance_type=self.type,
                    security_groups=[security_group],
                    instance_initiated_shutdown_behavior='stop')
        except boto.exception.EC2ResponseError as e:
            self.__log.critical(e.message)
            raise 'Unable to create AWS instance.'

        instance = res.instances[0]
        instance.add_tag('description', self.description)

        while instance.update() != 'running':
            time.sleep(10)

        self.id = instance.id
        self.public_dns = instance.public_dns_name

        return instance

    def __ssh_is_ready(self):
        '''
        Try to run an SSH command on the instance. A NetworkError means the
        instance is not ready to receive commands yet.
        '''
        try:
            with fabric.api.hide('everything'):
                fabric.api.run('ls')
            ready = True
        except fabric.exceptions.NetworkError:
            ready = False

        return ready

    def status(self):
        '''Get the status of the instance.'''
        return self.__instance.update()

    def start(self):
        '''Start the instance specified by inst_id.'''
        try:
            self.__instance.start()
        except boto.exception.EC2ResponseError as e:
            self.__log.critical(e.message)
            raise 'Unable to start AWS instance.'

        while self.status() != 'running':
            time.sleep(10)

        self.id = self.__instance.id
        self.public_dns = self.__instance.public_dns_name

    def stop(self):
        '''Stop the instance.'''
        try:
            self.__instance.stop()
        except boto.exception.EC2ResponseError as e:
            self.__log.critical(e.message)
            raise 'Unable to stop the AWS instance.'

        while self.status() != 'stopped':
            time.sleep(10)

    def terminate(self):
        '''Terminate the instance.'''
        try:
            return self.__instance.terminate()
        except boto.exception.EC2ResponseError as e:
            self.__log.critical(e.message)
            raise 'Unable to terminate the AWS instance.'

        while self.status() != 'terminated':
            time.sleep(10)

    def connect_ssh(self, pem):
        '''
        Configure fabric for SSH connections. Test the instance to see if it
        is ready to receive an SSH connection.
        '''
        fabric.api.env.user = self.user
        fabric.api.env.host_string = self.public_dns
        fabric.api.env.key_filename = pem

        while not self.__ssh_is_ready():
            time.sleep(10)

    def run_commands(self, commands):
        '''Run each of the commands.'''
        for command in commands:
            self.execute(command)

    def execute(self, command):
        with fabric.api.hide('output'):
            fabric.api.run(command)
