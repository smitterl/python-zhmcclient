# Copyright 2016 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import

import click

import zhmcclient
from .zhmccli import cli
from ._helper import print_properties, print_resources, abort_if_false, \
    COMMAND_OPTIONS_METAVAR
from ._cmd_cpc import find_cpc


def find_lpar(client, cpc_name, lpar_name):
    """
    Find an LPAR by name and return its resource object.
    """
    cpc = find_cpc(client, cpc_name)
    if cpc.dpm_enabled:
        raise click.ClickException("CPC %s is in DPM mode." % cpc_name)
    try:
        lpar = cpc.lpars.find(name=lpar_name)
    except zhmcclient.NotFound:
        raise click.ClickException("Could not find LPAR %s in CPC %s." %
                                   (lpar_name, cpc_name))
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    return lpar


@cli.group('lpar', options_metavar=COMMAND_OPTIONS_METAVAR)
def lpar_group():
    """
    Command group for managing LPARs.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """


@lpar_group.command('list', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.pass_obj
def lpar_list(cmd_ctx, cpc):
    """
    List the LPARs in a CPC.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_lpar_list(cmd_ctx, cpc))


@lpar_group.command('show', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('LPAR', type=str, metavar='LPAR')
@click.pass_obj
def lpar_show(cmd_ctx, cpc, lpar):
    """
    Show details of an LPAR in a CPC.

    In table format, some properties are skipped.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_lpar_show(cmd_ctx, cpc, lpar))


@lpar_group.command('update', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('LPAR', type=str, metavar='LPAR')
@click.option('--acceptable-status', type=str, required=False,
              help='The new set of acceptable operational status values. '
              'Default: No change.')
# TODO: Support multiple values for acceptable-status
@click.option('--next-activation-profile', type=str, required=False,
              help='The name of the new next image or load activation '
              'profile. '
              'Default: No change.')
# TODO: Add support for updating processor capping/sharing/weight related props
@click.option('--zaware-host-name', type=str, required=False,
              help='The new hostname for IBM zAware '
              '(only for LPARs in zaware activation mode). '
              'Default: No change.')
@click.option('--zaware-master-userid', type=str, required=False,
              help='The new master userid for IBM zAware '
              '(only for LPARs in zaware activation mode). '
              'Default: No change.')
@click.option('--zaware-master-password', type=str, required=False,
              help='The new master password for IBM zAware '
              '(only for LPARs in zaware activation mode). '
              'Default: No change.')
# TODO: Change zAware master password option to ask for password
# TODO: Add support for updating zAware network-related properties
@click.option('--ssc-host-name', type=str, required=False,
              help='The new hostname for the SSC appliance '
              '(only for LPARs in ssc activation mode). '
              'Default: No change.')
@click.option('--ssc-master-userid', type=str, required=False,
              help='The new master userid for the SSC appliance '
              '(only for LPARs in ssc activation mode). '
              'Default: No change.')
@click.option('--ssc-master-password', type=str, required=False,
              help='The new master password for the SSC appliance '
              '(only for LPARs in ssc activation mode). '
              'Default: No change.')
# TODO: Change SSC master password option to ask for password
# TODO: Add support for updating SSC network-related properties
@click.pass_obj
def lpar_update(cmd_ctx, cpc, lpar, **options):
    """
    Update the properties of an LPAR.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.

    Limitations:
      * The --acceptable-status option does not support multiple values.
      * The processor capping/sharing/weight related properties cannot be
        updated.
      * The network-related properties for zaware and ssc cannot beupdated.
      * The --zaware-master-password and --ssc-master-password options do not
        ask for the password.
    """
    cmd_ctx.execute_cmd(lambda: cmd_lpar_update(cmd_ctx, cpc, lpar, options))


@lpar_group.command('activate', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('LPAR', type=str, metavar='LPAR')
@click.pass_obj
def lpar_activate(cmd_ctx, cpc, lpar):
    """
    Activate an LPAR.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_lpar_activate(cmd_ctx, cpc, lpar))


@lpar_group.command('deactivate', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('LPAR', type=str, metavar='LPAR')
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              help='Skip prompt to confirm deactivation of the LPAR.',
              prompt='Are you sure you want to deactivate the LPAR ?')
@click.pass_obj
def lpar_deactivate(cmd_ctx, cpc, lpar):
    """
    Deactivate an LPAR.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_lpar_deactivate(cmd_ctx, cpc, lpar))


@lpar_group.command('load', options_metavar=COMMAND_OPTIONS_METAVAR)
@click.argument('CPC', type=str, metavar='CPC')
@click.argument('LPAR', type=str, metavar='LPAR')
@click.argument('LOAD-ADDRESS', type=str, metavar='LOAD-ADDRESS')
@click.pass_obj
def lpar_load(cmd_ctx, cpc, lpar, load_address):
    """
    Load (Boot, IML) an LPAR.

    In addition to the command-specific options shown in this help text, the
    general options (see 'zhmc --help') can also be specified right after the
    'zhmc' command name.
    """
    cmd_ctx.execute_cmd(lambda: cmd_lpar_load(cmd_ctx, cpc, lpar,
                                              load_address))


def cmd_lpar_list(cmd_ctx, cpc_name):
    client = zhmcclient.Client(cmd_ctx.session)
    cpc = find_cpc(client, cpc_name)
    if cpc.dpm_enabled:
        raise click.ClickException("CPC %s is in DPM mode." % cpc_name)
    try:
        lpars = cpc.lpars.list()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    print_resources(lpars, cmd_ctx.output_format)


def cmd_lpar_show(cmd_ctx, cpc_name, lpar_name):
    client = zhmcclient.Client(cmd_ctx.session)
    lpar = find_lpar(client, cpc_name, lpar_name)
    try:
        lpar.pull_full_properties()
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    skip_list = ('program-status-word-information')
    print_properties(lpar.properties, cmd_ctx.output_format, skip_list)


def cmd_lpar_update(cmd_ctx, cpc_name, lpar_name, options):

    client = zhmcclient.Client(cmd_ctx.session)
    lpar = find_lpar(client, cpc_name, lpar_name)

    name_map = {
        'next-activation-profile': 'next-activation-profile-name',
    }
    options = original_options(options)
    properties = options_to_properties(options, name_map)

    if not properties:
        click.echo("No properties specified for updating LPAR %s." % lpar_name)
        return

    try:
        lpar.update_properties(properties)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))

    # LPARs cannot be renamed.
    click.echo("LPAR %s has been updated." % lpar_name)


def cmd_lpar_activate(cmd_ctx, cpc_name, lpar_name):
    client = zhmcclient.Client(cmd_ctx.session)
    lpar = find_lpar(client, cpc_name, lpar_name)
    try:
        lpar.activate(wait_for_completion=True)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    click.echo('Activation of LPAR %s is complete.' % lpar_name)


def cmd_lpar_deactivate(cmd_ctx, cpc_name, lpar_name):
    client = zhmcclient.Client(cmd_ctx.session)
    lpar = find_lpar(client, cpc_name, lpar_name)
    try:
        lpar.deactivate(wait_for_completion=True)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    click.echo('Deactivation of LPAR %s is complete.' % lpar_name)


def cmd_lpar_load(cmd_ctx, cpc_name, lpar_name, load_address):
    client = zhmcclient.Client(cmd_ctx.session)
    lpar = find_lpar(client, cpc_name, lpar_name)
    try:
        lpar.load(load_address, wait_for_completion=True)
    except zhmcclient.Error as exc:
        raise click.ClickException("%s: %s" % (exc.__class__.__name__, exc))
    click.echo('Loading of LPAR %s is complete.' % lpar_name)
