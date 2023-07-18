#!/usr/bin/python3

import requests
import json
import os
import sys

from cachetools import cached, TTLCache

from extra import *

CLIENT_ID = get_env_secret(None, "CLIENT_ID")
CLIENT_SECRET = get_env_secret(None, "CLIENT_SECRET")
AUDIENCE = get_env_secret(None, "AUDIENCE")

headers = {"content-type": "application/x-www-form-urlencoded"}


def exchange_tokens(token):
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "audience": AUDIENCE,
        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
        "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
        "subject_token": token,
    }
    data = requests.post(
        url="https://auth.cern.ch/auth/realms/cern/protocol/openid-connect/token",
        data=data,
        headers=headers,
    )

    try:
        data_ = data.json()
        access_token = data_["access_token"]
        expires_in = data_["expires_in"]
        return {"access_token": access_token, "expires_in": expires_in}

    except Exception as e:
        return "Error: " + str(e)


def get_token(log):
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "audience": AUDIENCE,
        "grant_type": "client_credentials",
    }

    data = requests.post(
        url="https://auth.cern.ch/auth/realms/cern/protocol/openid-connect/token",
        data=data,
        headers=headers,
    )
    try:
        data_ = json.loads(data.text)
        access_token = data_["access_token"]
        data_access_token_and_expires_in = exchange_tokens(access_token)

        def get_expires_in_value():
            return data_access_token_and_expires_in["expires_in"]

        @cached(cache=TTLCache(maxsize=1, ttl=get_expires_in_value()))
        def get_access_token_value():
            return data_access_token_and_expires_in["access_token"]

        data_access_token = get_access_token_value()
        return data_access_token

    except Exception as e:
        log.warning(str(e))
        return "Error: " + str(e)
