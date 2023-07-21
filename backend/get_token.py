#!/usr/bin/python3
import requests
import logging
import cernrequests
from cachetools import cached, TTLCache
from backend.extra import *


headers = {"content-type": "application/x-www-form-urlencoded"}

logger = logging.getLogger(__name__)


def exchange_tokens(client_id: str, client_secret: str, audience: str, token: str):
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": audience,
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


def get_token(client_id: str, client_secret: str, audience: str) -> str:
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": audience,
        "grant_type": "client_credentials",
    }

    try:
        token, token_expiration = cernrequests.get_api_token(
            client_id=client_id,
            client_secret=client_secret,
            target_application=audience,
        )

        def get_expires_in_value() -> float:
            return token_expiration.timestamp()

        @cached(cache=TTLCache(maxsize=1, ttl=get_expires_in_value()))
        def get_access_token_value() -> str:
            return token

        data_access_token = get_access_token_value()
        return data_access_token

    except Exception as e:
        logger.warning(str(e))
        return "Error: " + str(e)
