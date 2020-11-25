#!/usr/bin/env python

import argparse
import coloredlogs, logging
import os
from pathlib import Path, PurePath
import sys

from jenkinsapi.jenkins import Jenkins
import yaml

home_dir = Path.home()
current_dir = Path()

CREDENTIALS_FILE = '.jenkins_job_watch'
CREDENTIALS_PATH = [str(PurePath(current_dir, CREDENTIALS_FILE)),
                    str(PurePath(home_dir, CREDENTIALS_FILE))]

DEFAULT_JOB = 'Test_Tower_Yolo_Express'

parser = argparse.ArgumentParser(description='Watch results of jenkins build')
parser.add_argument('--build', dest='build', type=int, required=True, help='Build id')
parser.add_argument('--job', dest='job', help='Job name')
parser.add_argument('--sorted', dest='sort_results', action="store_true", help='Sort results')
parser.add_argument('--jenkins-host', dest='jenkins_host', help='jenkins url')
parser.add_argument('--jenkins-username', dest='jenkins_username', help='jenkins username')
parser.add_argument('--jenkins-api-token', dest='jenkins_api_token', help='jenkins api token')
parser.add_argument('--verbose', '-v', action='count')

args = parser.parse_args()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

if args.verbose == 2:
    coloredlogs.install(level='DEBUG', logger=logger)
elif args.verbose == 1:
    coloredlogs.install(level='INFO', logger=logger)
else:
    coloredlogs.install(level='CRITICAL', logger=logger)

class Credentials:
    def __init__(self, host=None, username=None, token=None):
        self.host = host
        self.user = username
        self.token = token

creds = Credentials(args.jenkins_host, args.jenkins_username, args.jenkins_api_token)

class Config:
    def __init__(self, job=None, build=None, sort_results=None):
        self.job = job
        self.build = build
        self.sort_results = sort_results

config = Config(args.job, args.build, args.sort_results)

def load_missing_options_from_file(creds, config):
    """Update any missing credentials using any found in config file"""
    logger.debug(f'loading credentials')
    data = None
    for path in CREDENTIALS_PATH:
        try:
            with open(path, 'r') as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
                logger.debug(f'found credentials in {path}')
                break
        except Exception:
            pass

    keys = data.keys()
    if 'jenkins_host' in keys and creds.host is None:
        creds.host = data['jenkins_host']
        logger.debug(f'jenkins_host: {creds.host}')
    if 'username' in keys and creds.user is None:
        creds.user = data['username']
        logger.debug(f'username: {creds.user}')
    if 'token' in keys and creds.token is None:
        creds.token = data['token']
        logger.debug(f'token: <omitted>')

    if not creds.host:
        raise Exception('Jenkins url required')
    if not creds.user:
        raise Exception('Jenkins username required')
    if not creds.token:
        raise Exception('Jenkins token required')

    if config.job is None:
        if 'job' in keys:
            config.job = data['job']
        else:
            config.job = DEFAULT_JOB
    logger.debug(f'job: {config.job}')

    if not config.job:
        raise Exception('Test Job name required')

def get_server_instance(creds):
    logger.debug(f'connecting to {creds.host}')
    server = Jenkins(creds.host, username=creds.user, password=creds.token)
    return server

def get_build(server, job_name, build_number):
    logger.debug(f'getting build {build_number} for {job_name}')
    job = server.get_job(job_name)
    return job.get_build(build_number)

def get_build_metadata(build, suppress_description=False):
    desc = [f"{build.get_build_url()}"]
    if not suppress_description:
        desc.append(f"{build.get_description()}")
    desc.append(f"{str(build.get_timestamp().date())}")
    return '\n'.join(desc)

def get_console_output(build):
    logger.info(f'getting console output for build {build.get_number()}')
    return build.get_console()

def filter_failures(console_output):
    failures = []

    for line in console_output.split('\n'):
        logger.debug(f'parsing line: {line}')
        if 'FAILED tests' in line:
            logger.debug(f' .. line shows a failure')
            # strip all text except testcase name
            index = line.rindex('::') + 2
            failure = line[index:].strip()
            failures.append(failure)
    return set(failures)  # ensure failures are unique

if __name__ == "__main__":
    load_missing_options_from_file(creds, config)
    server = get_server_instance(creds)
    build = get_build(server, config.job, config.build)

    print("Getting results for:")
    print(get_build_metadata(build) + '\n')

    console_output = get_console_output(build)
    failures = filter_failures(console_output)
    if config.sort_results:
        failures = sorted(failures)

    print(f'Failures:')
    for index, failure in enumerate(failures, start=1):
        print(f'{index : >3}   {failure}')
