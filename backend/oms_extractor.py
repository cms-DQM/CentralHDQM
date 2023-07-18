#!/usr/bin/env python3

import requests
import get_token

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FIELDS = "start_time,end_time,b_field,energy,delivered_lumi,end_lumi,recorded_lumi,l1_key,hlt_key,l1_rate,hlt_physics_rate,duration,fill_number,fill_type_runtime,stable_beam"
OMS_URL = (
    "https://cmsoms.cern.ch/agg/api/v1/runs?filter[run_number][eq]=%s&fields=" + FIELDS
)
HEADERS = None


def get_oms_run(run, log):
    log.info("Get OMS data for run %s ..." % run)
    url = OMS_URL % run

    oms_data = ""
    try:
        global HEADERS
        if not HEADERS:
            token = get_token.get_token(log)
            HEADERS = {"Authorization": "Bearer %s" % (token)}

        try:
            response = requests.get(url, headers=HEADERS, verify=False)
            oms_runs_json = response.json()
        except:
            token = get_token.get_token(log)
            HEADERS = {"Authorization": "Bearer %s" % (token)}
            response = requests.get(url, headers=HEADERS, verify=False)
            oms_runs_json = response.json()

        oms_attributes = oms_runs_json["data"][0]["attributes"]
        oms_attributes_meta = None

        try:
            oms_attributes_meta = oms_runs_json["data"][0]["meta"]["row"]
        except Exception as error_log:
            log.warning(
                "Failed to get OMS meta for run %s ..., skip without units" % run
            )
            log.warning("Error ... %s " % error_log)
            units = "0"

        if oms_attributes_meta:
            lumis = ["delivered_lumi", "recorded_lumi", "end_lumi"]
            for lumi in lumis:
                if lumi not in oms_attributes_meta:
                    continue
                if "units" not in oms_attributes_meta[lumi]:
                    continue
                oms_attributes[lumi] = (
                    str(oms_attributes[lumi])
                    + " x "
                    + oms_attributes_meta[lumi]["units"]
                )

        oms_data = oms_attributes

    except Exception as error_log:
        log.warning("Failed to get OMS data for run %s ..." % run)
        log.warning("Error ... %s " % error_log)
        return 1

    return oms_data
