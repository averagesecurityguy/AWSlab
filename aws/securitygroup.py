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
import logging
import boto.ec2

class SecurityGroup():
    def __init__(self, name, conn):
        '''
        Create a connection to an AWS region and add the security group if it
        doesn't exist.
        '''
        self.__log = logging.getLogger('SecurityGroup')
        self.name = name
        self.desc = 'Auto-created security group for {0}.'.format(self.name)
        self.__conn = conn
        self.__sg = self.__get_security_group()
        self.add_rule('tcp', 22, 22, '0.0.0.0/0')

    def __get_aws_groups(self, name=[]):
        '''Return a list of AWS security groups.'''
        try:
            groups = self.__conn.get_all_security_groups(groupnames=name)
        except boto.exception.EC2ResponseError as e:
            self.__log.critical(e.message)
            raise 'Unable to get AWS security groups.'

        return groups

    def __create_aws_group(self):
        '''Create a new AWS security group.'''
        try:
            self.__conn.create_security_group(self.name, self.desc)
        except boto.exception.EC2ResponseError as e:
            self.__log.critical(e.message)
            raise 'Could not create AWS security group.'

    def __get_security_group(self):
        '''
        Return a boto.ec2.securitygroup.SecurityGroup object. Create the 
        security group first, if necessary.
        ''' 
        groups = self.__get_aws_groups()
        if self.name not in [g.name for g in groups]:
            self.__create_aws_group()

        return self.__get_aws_groups(self.name)[0]

    def add_rule(self, protocol, start, end, source):
        '''Add a new rule to the security group, if it doesn't exist.'''
        try:                
            self.__sg.authorize(ip_protocol=protocol,
                                from_port=start,
                                to_port=end,
                                cidr_ip=source)
        except boto.exception.EC2ResponseError as e:
            self.__log.warning(e.message)

    def remove_rule(self, protocol, start, end, source):
        '''Remove a rule from the security group.'''
        try:         
            self.__sg.revoke(ip_protocol=protocol,
                             from_port=start,
                             to_port=end,
                             cidr_ip=source)
        except boto.exception.EC2ResponseError as e:
            self.__log.warning(e.message)

    def add_rules(self, rules):
        '''Add each rule in the list to the security group.'''
        for rule in rules:
            self.add_rule(rule[0], rule[1], rule[2], rule[3])

    def remove_rules(self, rules):
        '''Remove each rule in the list from the security group.'''
        for rule in rules:
            self.remove_rule(rule[0], rule[1], rule[2], rule[3])

    def remove(self):
        '''Remove the security group from the region.'''
        try:
            self.__sg.delete()
        except boto.exception.EC2ResponseError as e:
            self.__log.error(e.message)
