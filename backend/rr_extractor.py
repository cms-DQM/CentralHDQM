#!/usr/bin/env python3
import os
import json
import logging
import requests
from dotenv import load_dotenv
from .get_token import get_token


load_dotenv()

logger = logging.getLogger(__name__)

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
AUDIENCE = "cmsrunregistry-sso-proxy"

MIN_LUMI_FOR_COLLISIONS = 0.1
MIN_DURATION_FOR_COSMICS = 3600


def _get_headers(token: str = None) -> str:
    headers = {"Content-type": "application/json"}
    headers["Authorization"] = "Bearer " + token
    return headers


def is_significant(rr_data, rr_run_class) -> bool:
    """
    Logic to determine if run is significant for HDQM:
    1. If HLT key contains string "special", run is not significant
    2. For collision runs integrated luminosity has to be greater than 0.1 1/pb
    3. For cosmic runs duration has to be longer than 1 hour
    """
    if "oms_attributes" not in rr_data:
        return False

    if "hlt_key" in rr_data:
        if "special" in rr_data["oms_attributes"]["hlt_key"].lower():
            return False

    if "collision" in rr_run_class.lower():
        if "recorded_lumi" in rr_data["oms_attributes"]:
            if rr_data["oms_attributes"]["recorded_lumi"]:
                if (
                    rr_data["oms_attributes"]["recorded_lumi"]
                    >= MIN_LUMI_FOR_COLLISIONS
                ):
                    return True

    if "cosmic" in rr_run_class.lower():
        if "duration" in rr_data["oms_attributes"]:
            if rr_data["oms_attributes"]["duration"]:
                if rr_data["oms_attributes"]["duration"] >= MIN_DURATION_FOR_COSMICS:
                    return True

    return False


def get_rr_run(run: int) -> dict:
    """
    Why not use the runregistry python package?
    """
    logger.info("Get RR data for run %s ..." % run)
    # TODO: replace with production one once 1.0.0 runregistry is published.
    url = "https://cmsrunregistry-qa.web.cern.ch/api/runs_filtered_ordered"
    request = """
    { 
        "page" : 0,
        "page_size" : 100000,
        "sortings" : [],
        "filter" : {
        "run_number" : %s ,
        "rr_attributes.significant" : true
        }
    }
    """ % (
        run
    )
    try:
        token = get_token(CLIENT_ID, CLIENT_SECRET, AUDIENCE)
        response = requests.post(
            url, json=json.loads(request), headers=_get_headers(token)
        )

        try:
            result_json = json.loads(response.text)
            results_runs = result_json["runs"]

            if not len(results_runs):
                # no info about the run in RR
                return {"rr_run_class": "RR unknown", "rr_significant": False}

            rr_data = results_runs[0]
            rr_run_class = rr_data["rr_attributes"]["class"]
            try:
                rr_significant = is_significant(rr_data, rr_run_class)
            except Exception as error_log:
                logger.warning(
                    "Cant check significance in RR data for run %s ..., will think as not significant"
                    % run
                )
                logger.warning("Error ... %s " % error_log)
                logger.warning('RR answer = "%s" ' % response.text)
                rr_significant = False

            answer = {"rr_run_class": rr_run_class, "rr_significant": rr_significant}
            return answer
        except Exception as error_log:
            logger.warning("Failed to get RR data for run %s ..." % run)
            logger.warning("Error ... %s " % error_log)
            logger.warning('RR answer = "%s" ' % response.text)
            return 1

    except Exception as error_log:
        logger.warning("Failed to get RR data for run %s ..." % run)
        logger.warning("Error ... %s " % error_log)
        return 1
