#!/usr/bin/env python3
# Copyright (C) 2017  Qrama, developed by Tengu-team
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# pylint: disable=c0111,c0103,c0301
import os
import shutil
from subprocess import check_call, CalledProcessError
from charmhelpers.core.templating import render
from charmhelpers.core.hookenv import local_unit, status_set, config, open_port, application_version_set, unit_public_ip
from charmhelpers.core.host import service_restart
from charms.reactive import when, when_not, set_state, remove_state


CONFIG_DIR = '/etc/sensu/conf.d'
SSL_DIR = '/etc/sensu/ssl'


@when('apt.installed.sensu', 'info.available')
@when_not('sensu.installed')
def setup_sensu(info):
    application_version_set('0.29')
    rabbitmq = {'host': config()['rabbitmq'].split(':')[0],
                'port': config()['rabbitmq'].split(':')[1],
                'password': config()['password']}
    if config()['ssl_key'] != '':
        if not os.path.isdir(SSL_DIR):
            os.mkdir(SSL_DIR)
        with open('{}/ssl_key.pem'.format(SSL_DIR), 'w+') as ssl_key:
            ssl_key.write(config()['ssl_key'])
        with open('{}/ssl_cert.pem'.format(SSL_DIR), 'w+') as ssl_cert:
            ssl_cert.write(config()['ssl_cert'])
        rabbitmq['ssl_cert'] = '{}/ssl_cert.pem'.format(SSL_DIR)
        rabbitmq['ssl_key'] = '{}/ssl_key.pem'.format(SSL_DIR)
    name = '{}/{}'.format(os.environ['JUJU_MODEL_NAME'], os.environ['JUJU_MACHINE_ID'])
    application = os.environ['JUJU_REMOTE_UNIT']
    unit = local_unit().replace('/', '-')
    render('rabbitmq.json', '{}/rabbitmq.json'.format(CONFIG_DIR), context=rabbitmq)
    client = {'name': name, 'public_ip': unit_public_ip(), 'subscriptions': '[\"monitoring\"]'}
    render('client.json', '{}/client.json'.format(CONFIG_DIR), context=client)
    render('transport.json', '{}/transport.json'.format(CONFIG_DIR), context={})
    for plugin in config()['plugins'].split(' '):
        try:
            check_call(['sensu-install', '-p', plugin])
        except CalledProcessError as e:
            status_set('blocked', e.output)
    if not os.path.isdir(os.path.join(CONFIG_DIR, unit)):
        os.mkdir(os.path.join(CONFIG_DIR, unit))
    measurements = config()['measurements'].split(' ')
    try:
        checks = [
            {'type': m.split('|')[0], 'script': m.split('|')[1], 'subscribers': application} for m in measurements
        ]
        render('checks.json', '{}/{}/checks.json'.format(CONFIG_DIR, unit), context={'checks': checks})
        # When multiple sensu-clients are being used to monitor different sets of measurements,
        # open port would fail. Downside of this check is that juju status will not provide correct
        # info about open ports, except for the first Sensu client.
        try:
            open_port(3030)
        except CalledProcessError:
            pass
        service_restart('sensu-client')
        status_set('active', 'active (ready)')
        set_state('sensu.installed')
    except IndexError:
        status_set('blocked', 'Incorrect checks given in config')


@when('sensu.installed')
@when_not('info.available')
def remove():
    shutil.rmtree(os.path.join(CONFIG_DIR, local_unit().replace('/', '-')))
    service_restart('sensu-client')
    remove_state('sensu.installed')
