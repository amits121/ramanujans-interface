"""Contact form receiver for a static site built by the engine (pattern S-07).

Deployed by the founder as an AWS Lambda function (Python 3.12, arm64) with a function URL (auth NONE) in the
site's account. The static page posts name, email and message here as a plain HTML form; nothing runs in the
browser. The function validates the three fields, sends one email through Amazon SES to TO_ADDRESS with the
sender's address as reply-to, and answers with a small confirmation page in the site's colours.

Environment: TO_ADDRESS (where messages go), FROM_ADDRESS (an SES verified identity, e.g. contact@techinnovations.io),
SITE_URL (e.g. https://techinnovations.io), CONTACT_PATH (default /about/contact/).
Role: ses:SendEmail on the sending identity. Reserved concurrency 2 keeps a flood from costing anything.

Copyright (c) 2026 Intelligent Cloud Lab Inc.
"""
import base64
import html
import os
import re
import urllib.parse

import boto3

EMAIL = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]{2,}$')
LIMITS = {'name': 200, 'email': 254, 'message': 5000}
ses = boto3.client('sesv2')


def handler(event, context):
    body = event.get('body') or ''
    if event.get('isBase64Encoded'):
        body = base64.b64decode(body).decode('utf-8', 'replace')
    form = urllib.parse.parse_qs(body, keep_blank_values=True)
    fields = {k: form.get(k, [''])[0].strip()[:LIMITS[k]] for k in LIMITS}
    if not fields['name'] or not EMAIL.match(fields['email']) or len(fields['message']) < 10:
        return page(400, 'Please give your name, a valid email address and a message of at least ten characters.')
    ses.send_email(
        FromEmailAddress=os.environ['FROM_ADDRESS'],
        Destination={'ToAddresses': [os.environ['TO_ADDRESS']]},
        ReplyToAddresses=[fields['email']],
        Content={'Simple': {
            'Subject': {'Data': f'{os.environ.get("SITE_URL", "site")} contact: {fields["name"]}'},
            'Body': {'Text': {'Data': f'From: {fields["name"]} <{fields["email"]}>\n\n{fields["message"]}\n'}}}})
    return page(200, 'Message received. All inquiries receive structured technical responses within two business days.')


def page(status, text):
    site = os.environ.get('SITE_URL', '')
    back = site + os.environ.get('CONTACT_PATH', '/about/contact/')
    brand = site.replace('https://', '').replace('http://', '') or 'contact'
    body = (f'<!doctype html><html lang="en"><head><meta charset="utf-8" />'
            f'<meta name="viewport" content="width=device-width, initial-scale=1" /><title>{html.escape(brand)}</title>'
            f'<style>body{{margin:0;font-family:"IBM Plex Sans","Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:#000;background:#fff}}'
            f'header{{background:#750014;color:#fff;padding:16px 24px;font-weight:700}}'
            f'main{{max-width:720px;margin:0 auto;padding:80px 16px;font-size:17px;line-height:1.7}}a{{color:#750014}}</style></head>'
            f'<body><header>{html.escape(brand)}</header><main><p>{html.escape(text)}</p>'
            f'<p><a href="{html.escape(back)}">Back to the contact page</a></p></main></body></html>')
    return {'statusCode': status, 'headers': {'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store'}, 'body': body}
