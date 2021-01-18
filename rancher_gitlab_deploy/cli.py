#!/usr/bin/env python
import logging
import sys
import time
import json

import click
import requests

from requests import HTTPError


try:
    from httplib import HTTPConnection  # py2
except ImportError:
    from http.client import HTTPConnection  # py3


@click.command()
@click.option(
    "--rancher-url",
    envvar="RANCHER_URL",
    required=True,
    help="The URL for your Rancher server, eg: http://rancher:8000",
)
@click.option(
    "--rancher-key",
    envvar="RANCHER_ACCESS_KEY",
    required=True,
    help="The environment or account API key",
)
@click.option(
    "--rancher-secret",
    envvar="RANCHER_SECRET_KEY",
    required=True,
    help="The secret for the access API key",
)
@click.option(
    "--rancher-label-separator",
    envvar="RANCHER_LABEL_SEPARATOR",
    required=False,
    default=",",
    help="Where the default separator (',') could cause issues",
)
@click.option(
    "--environment",
    default=None,
    help="The name of the environment to add the host into "
    + "(only needed if you are using an account API key instead of an environment API key)",
)
@click.option(
    "--projecturl",
    envvar="CI_PROJECT_URL",
    default=None,
    required=True,
    help="The name of the stack in Rancher (defaults to the name of the group in GitLab)",
)
@click.option(
    "--service",
    envvar="CI_PROJECT_NAME",
    default=None,
    required=False,
    help="The name of the service in Rancher to upgrade (defaults to the name of the service in GitLab)",
)
@click.option(
    "--start-before-stopping/--no-start-before-stopping",
    default=False,
    help="Should Rancher start new containers before stopping the old ones?",
)
@click.option(
    "--batch-size",
    default=1,
    help="Number of containers to upgrade at once",
)
@click.option(
    "--batch-interval",
    default=2,
    help="Number of seconds to wait between upgrade batches",
)
@click.option(
    "--upgrade-timeout",
    default=5 * 60,
    help="How long to wait, in seconds, for the upgrade to finish before exiting. To skip the wait, pass the --no-wait-for-upgrade-to-finish option.",
)
@click.option(
    "--wait-for-upgrade-to-finish/--no-wait-for-upgrade-to-finish",
    default=True,
    help="Wait for Rancher to finish the upgrade before this tool exits",
)
@click.option(
    "--rollback-on-error/--no-rollback-on-error",
    default=False,
    help="Rollback the upgrade if an error occured. The rollback will be performed only if the option --wait-for-upgrade-to-finish is passed",
)
@click.option(
    "--new-image",
    default=None,
    help="If specified, replace the image (and :tag) with this one during the upgrade",
)
@click.option(
    "--finish-upgrade/--no-finish-upgrade",
    default=True,
    help="Mark the upgrade as finished after it completes",
)
@click.option(
    "--sidekicks/--no-sidekicks",
    default=False,
    help="Upgrade service sidekicks at the same time",
)
@click.option(
    "--new-sidekick-image",
    default=None,
    multiple=True,
    help="If specified, replace the sidekick image (and :tag) with this one during the upgrade",
    type=(str, str),
)
@click.option(
    "--create/--no-create",
    default=False,
    help="If specified, create Rancher stack and service if they don't exist",
)
@click.option(
    "--labels",
    default=None,
    help="If specified, add a comma separated list of key=values to add to the service",
)
@click.option(
    "--label",
    default=None,
    multiple=True,
    help="If specified, add a Rancher label to the service",
    type=(str, str),
)
@click.option(
    "--variables",
    default=None,
    help="If specified, add a comma separated list of key=values to add to the service",
)
@click.option(
    "--variable",
    default=None,
    multiple=True,
    help="If specified, add a environment variable to the service",
    type=(str, str),
)
@click.option(
    "--service-links",
    default=None,
    help="If specified, add a comma separated list of key=values to add to the service",
)
@click.option(
    "--service-link",
    default=None,
    multiple=True,
    help="If specified, add a service link to the service",
    type=(str, str),
)
@click.option(
    "--host-id",
    default=None,
    help="If specified, service will be deployed on requested host",
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable HTTP Debugging",
)
@click.option(
    "--ssl-verify/--no-ssl-verify",
    default=True,
    help="Disable certificate checks. Use this to allow connecting to a HTTPS Rancher server using an self-signed certificate",
)
@click.option(
    "--secrets",
    default=None,
    help="If specified, add a comma separated list of secrets to the service",
)
@click.option(
    "--secret",
    default=None,
    multiple=True,
    help="If specified add a secret to the service",
)
@click.option(
    "--image",
    envvar="RANCHER_IMAGE_NAME",
    default=None,
    help="imagename",
)
def main(
    rancher_url,
    rancher_key,
    rancher_secret,
    rancher_label_separator,
    environment,
    projecturl,
    service,
    new_image,
    batch_size,
    batch_interval,
    start_before_stopping,
    upgrade_timeout,
    wait_for_upgrade_to_finish,
    rollback_on_error,
    finish_upgrade,
    sidekicks,
    new_sidekick_image,
    create,
    labels,
    label,
    variables,
    variable,
    service_links,
    service_link,
    host_id,
    debug,
    ssl_verify,
    secrets,
    secret,
    image
):
    """Performs an in service upgrade of the service specified on the command line"""
    if debug:
        debug_requests_on()

    # split url to protocol and host
    if "://" not in rancher_url:
        bail("The Rancher URL doesn't look right")

    proto, host = rancher_url.split("://")
    api = "%s://%s/v3" % (proto, host)


    session = requests.Session()

    # Set verify based on --ssl-verify/--no-ssl-verify option
    session.verify = ssl_verify

    # 0 -> Authenticate all future requests
    session.auth = (rancher_key, rancher_secret)
    # Check for labels and environment variables to set
    upgrade_url = "%s/%s" % (api,projecturl)
    pr = session.get(upgrade_url)
    upgrade_data = pr.json()
    upgrade_data['containers'][0]['image']=image
    headers = {'Content-Type': 'application/json'}
    ur = session.put(upgrade_url,headers=headers,data=json.dumps(upgrade_data))
    msg(ur.status_code)
    sys.exit(0)


def msg(message):
    click.echo(click.style(message, fg="green"))


def warn(message):
    click.echo(click.style(message, fg="yellow"))


def bail(message, exit=True):
    click.echo(click.style("Error: " + message, fg="red"))
    if exit:
        sys.exit(1)


def debug_requests_on():
    """Switches on logging of the requests module."""
    HTTPConnection.debuglevel = 1

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True