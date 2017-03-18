#!/usr/bin/python -tt
# vim: fileencoding=utf8

import logging
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..")))

import email.parser
import pytest

import encryptmail.common
from encryptmail.common import Mail, setup_logging, set_logging_level



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

def test_loglevel():
    setup_logging(level=logging.INFO)
    assert encryptmail.common.console_logger.level == logging.INFO
    set_logging_level("debug")
    assert encryptmail.common.console_logger.level == logging.DEBUG
    set_logging_level("warn")
    assert encryptmail.common.console_logger.level == logging.WARN

    with pytest.raises(AttributeError):
        set_logging_level("invalid_test")

def test_fqdnify():
    mail = open("tests/mails/03-no-fqdn-to.eml", "rb").read()
    message = email.parser.Parser().parsestr(mail)
    assert "root, nobody@example.com" == message["To"]
    assert "nobody" == message["From"]
    encryptmail.common.fqdnify_headers(message, "fqdn.example.com")
    assert "root@fqdn.example.com, nobody@example.com" == message["To"]
    assert "nobody@fqdn.example.com" == message["From"]
