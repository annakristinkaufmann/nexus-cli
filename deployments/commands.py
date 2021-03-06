import click
import re
import requests
import json
from blessings import Terminal
from prettytable import PrettyTable

import config_utils
import nexus_utils
import utils


t = Terminal()


def is_valid_deployment_name(name, reg=re.compile('^[a-zA-Z0-9\.\-_]+$')):
    return bool(reg.match(name))


@click.command()
@click.option('--add', '-a', help='Name of the nexus deployment to be locally added')
@click.option('--remove', '-r', help='Name of the nexus deployment to be locally removed')
@click.option('--select', '-r', help='Name of the nexus deployment to be selected for subsequent CLI calls')
@click.option('--url', '-u', help='URL of a nexus deployment (for --add, --remove)')
@click.option('--list', '-l', is_flag=True, help='List all nexus deployment locally registered')
@click.option('--count', '-c', is_flag=True, default=False, help='Show count of entities when listing')
@click.option('--public-only', '-p', is_flag=True, default=False, help='Count only public entities (i.e. no authentication)')
def deployments(add, remove, select, url, list, count, public_only):
    """Manage Nexus deployments."""
    if add is not None and remove is not None:
        utils.error("You cannot add and remove on the same command line.")

    if add is not None:
        # print('add:' + add)
        if url is None:
            utils.error("You must have a URL (--url) in order to add a deployment")
        config = config_utils.get_cli_config()
        if add in config and 'url' in config[add]:
            utils.error("This deployment already exist (%s) with url: %s" % (add, config[add]))

        # Validate URL
        data_url = url.rstrip("/") + '/v0/data'
        r = requests.get(data_url)
        if r.status_code != 200:
            utils.error("Failed to get entity count from URL: " + data_url +
                        '\nRequest status: ' + str(r.status_code))

        config[add] = {'url': url.rstrip("/")}
        config_utils.save_cli_config(config)

    if remove is not None:
        # print('remove:'+remove)
        if url is not None:
            utils.error("--remove doesn't take a URL")

        config = config_utils.get_cli_config()
        if remove not in config:
            utils.error("Could not find deployment '%s' in CLI config" % remove)

        config.pop(remove, None)
        config_utils.save_cli_config(config)

    if select is not None:
        # print('select')
        if select is None:
            utils.error("No deployment name given")
        config = config_utils.get_cli_config()
        if select not in config:
            utils.error("Unknown deployment: " + select)
        for key in config.keys():
            if 'selected' in config[key] and key != select:
                config[key].pop('selected', None)
                print("deployment '%s' was unselected" % key)
        config[select]['selected'] = True
        config_utils.save_cli_config(config)

    if list is True:
        config = config_utils.get_cli_config()
        if count:
            if public_only:
                scope = 'public'
            else:
                scope = 'authenticated'
            table = PrettyTable(['Deployment', 'Selected', 'URL', '#entities (' + scope + ')'])
        else:
            table = PrettyTable(['Deployment', 'Selected', 'URL'])
        table.align["Deployment"] = "l"
        table.align["URL"] = "l"
        for key in config.keys():
            selected = ""

            if 'selected' in config[key] and config[key]['selected'] is True:
                selected = "Yes"

            total = '-'
            if count:
                data_url = config[key]['url'] + '/v0/data'
                authenticate = not public_only
                results, total = nexus_utils.get_results_by_uri(data_url, first_page_only=True, authenticate=authenticate)

                table.add_row([key, selected, config[key]['url'], format(total, ',d')])
            else:
                table.add_row([key, selected, config[key]['url']])

        print(table)
