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
import os
import logging
import boto.ec2

class KeyPair():
    def __init__(self, name, path, conn):
        '''
        Create a new key pair in the specified region if it doesn't exist.
        '''
        self.__log = logging.getLogger('KeyPair')
        self.name = name
        self.path = path
        self.pem = os.path.join(path, name) + '.pem'
        self.__conn = conn

        self.__verify_ssh_path()
        self.create_key()


    def __verify_ssh_path(self):
        if not (os.path.exists(self.path) and os.path.isdir(self.path)):
            e = '{0} does not exist or is not a directory.'.format(self.path)
            self.__log.critical(e)
            raise 'Invalid SSH path'

    def __get_aws_keypairs(self):
        try:
            keys = self.__conn.get_all_key_pairs()
        except boto.exception.EC2ResponseError as e:
            self.__log.critical(e.message)
            raise 'Unable to get AWS key pairs.'

        return keys

    def __create_aws_keypair(self):
        try:
            key = self.__conn.create_key_pair(self.name)
        except boto.exception.EC2ResponseError as e:
            self.__log.critical(e.message)
            raise 'Unable to create AWS key pair.'

        self.__log.info('Key pair {0} was created.'.format(self.name))
        return key

    def create_key(self):        
        keys = self.__get_aws_keypairs()

        if self.name not in [k.name for k in keys]:
            key = self.__create_aws_keypair()
            key.save(self.path)

    def remove(self):
        '''Remove the key pair.'''
        try:                
            self.__conn.delete_key_pair(self.name)
        except boto.exception.EC2ResponseError as e:
            self.__log.error(e.message)

