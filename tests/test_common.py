#!/usr/bin/python -tt
# vim: fileencoding=utf8

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..")))


from encryptmail.common import Mail


def parse_mail(fromaddr, recipients, message):
    mail = Mail(fromaddr, recipients, message=message)
    jsondata = mail.json
    mailfromjson = Mail(json_=jsondata)
    assert mailfromjson.message == message
    assert mailfromjson.fromaddr == mailfromjson.fromaddr
    assert mailfromjson.recipients == mailfromjson.recipients


def test_mail_to_json():
    message = open("tests/mails/00-ascii.eml", "rb").read()
    parse_mail("from@example.com", ["to@example.com"], message=message)
    message = open("tests/mails/01-utf8.eml", "rb").read()
    parse_mail("from@example.com", ["to@example.com"], message=message)
    message = open("tests/mails/02-latin1.eml", "rb").read()
    parse_mail("from@example.com", ["to@example.com"], message=message)
