#!/usr/bin/env python3
"""
Deploy one site to the web host: gated build, upload to the sites bucket, site-sync on the host
through Systems Manager Run Command, then prove the served bytes equal the build.

    python scripts/deploy_site.py engine/specs/sample-landing.yaml sample-landing \
        --host inovations.techinnovations.io [--profile icl-2] [--bucket icl-sites-<account>] \
        [--instance-name icl-web-host] [--title "..."] [--description "..."] [--skip-build] [--http]

Writes to the company account (the bucket upload and the Run Command) run under the given profile,
on the founder's word. Nothing here touches the engine: the build is scripts/build_site.py.

Copyright (c) 2026 Intelligent Cloud Lab Inc.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    with open(path, 'rb') as f:
        return sha256_bytes(f.read())


def aws(args, profile, region, parse=True):
    cmd = ['aws', '--profile', profile, '--region', region, '--output', 'json'] + args
    out = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
    return json.loads(out) if parse and out.strip() else out


def build(spec, site, title, description):
    cmd = [sys.executable, os.path.join(ROOT, 'scripts', 'build_site.py'), spec, site]
    if title:
        cmd += ['--title', title]
    if description:
        cmd += ['--description', description]
    subprocess.run(cmd, check=True)


def manifest(out_dir):
    rows = {}
    for dirpath, dirs, files in os.walk(out_dir):
        dirs[:] = [d for d in dirs if d != 'preview']
        for name in files:
            path = os.path.join(dirpath, name)
            rows[os.path.relpath(path, out_dir)] = sha256_file(path)
    return rows


def upload(out_dir, bucket, site, profile, region):
    subprocess.run(['aws', '--profile', profile, '--region', region, 's3', 'sync', out_dir + '/',
                    f's3://{bucket}/{site}/', '--delete', '--exclude', 'preview/*', '--only-show-errors'],
                   check=True)


def instance_id(name, profile, region):
    data = aws(['ec2', 'describe-instances', '--filters', f'Name=tag:Name,Values={name}',
                'Name=instance-state-name,Values=running'], profile, region)
    ids = [i['InstanceId'] for r in data['Reservations'] for i in r['Instances']]
    if len(ids) != 1:
        sys.exit(f'expected one running instance named {name}, found {ids}')
    return ids[0]


def run_sync(iid, site, profile, region):
    sent = aws(['ssm', 'send-command', '--instance-ids', iid, '--document-name', 'AWS-RunShellScript',
                '--comment', f'site-sync {site}', '--parameters',
                json.dumps({'commands': [f'/usr/local/bin/site-sync {site}']})], profile, region)
    cid = sent['Command']['CommandId']
    for _ in range(60):
        time.sleep(3)
        try:
            inv = aws(['ssm', 'get-command-invocation', '--command-id', cid, '--instance-id', iid], profile, region)
        except subprocess.CalledProcessError:
            continue
        if inv['Status'] in ('Success', 'Failed', 'Cancelled', 'TimedOut'):
            print(inv.get('StandardOutputContent', '').strip())
            if inv['Status'] != 'Success':
                print(inv.get('StandardErrorContent', '').strip())
                sys.exit(f'site-sync {inv["Status"]}')
            return
    sys.exit('site-sync did not finish in time')


def verify(host, scheme, rows):
    mismatches = 0
    for rel in ('index.html',) + tuple(r for r in sorted(rows) if r.startswith('assets/')):
        url = f'{scheme}://{host}/' + ('' if rel == 'index.html' else rel)
        req = urllib.request.Request(url, headers={'Accept-Encoding': 'identity', 'User-Agent': 'deploy-check'})
        with urllib.request.urlopen(req, timeout=20) as resp:
            served = sha256_bytes(resp.read())
        ok = served == rows[rel]
        mismatches += 0 if ok else 1
        print(f'  {"MATCH" if ok else "DIFFER"}  {rel}  served {served[:16]}  build {rows[rel][:16]}')
    return mismatches == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('spec')
    ap.add_argument('site')
    ap.add_argument('--host', required=True, help='the host name the site is served on')
    ap.add_argument('--profile', default='icl-2')
    ap.add_argument('--region', default='us-east-1')
    ap.add_argument('--bucket', default='')
    ap.add_argument('--instance-name', default='icl-web-host')
    ap.add_argument('--title', default='')
    ap.add_argument('--description', default='')
    ap.add_argument('--skip-build', action='store_true', help='deploy the existing build/<site>')
    ap.add_argument('--http', action='store_true', help='verify over http (before the certificate exists)')
    args = ap.parse_args()

    out_dir = os.path.join(ROOT, 'build', args.site)
    if not args.skip_build:
        build(args.spec, args.site, args.title, args.description)
    if not os.path.isfile(os.path.join(out_dir, 'index.html')):
        sys.exit(f'no build at {out_dir}')
    rows = manifest(out_dir)
    print(f'build {out_dir}: {len(rows)} files, index.html {rows["index.html"][:16]}')

    bucket = args.bucket or 'icl-sites-' + aws(['sts', 'get-caller-identity'], args.profile, args.region)['Account']
    upload(out_dir, bucket, args.site, args.profile, args.region)
    print(f'uploaded to s3://{bucket}/{args.site}/')

    iid = instance_id(args.instance_name, args.profile, args.region)
    run_sync(iid, args.site, args.profile, args.region)

    scheme = 'http' if args.http else 'https'
    if verify(args.host, scheme, rows):
        print(f'deployed {args.site} to {scheme}://{args.host}/  served bytes equal the build')
    else:
        sys.exit('served bytes differ from the build')


if __name__ == '__main__':
    main()
