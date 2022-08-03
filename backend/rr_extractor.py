#!/usr/bin/env python3
import json
import requests
import cernrequests

CERT='/data/hdqm2/private/usercert.pem'
KEY='/data/hdqm2/private/userkey.pem'

MIN_LUMI_FOR_COLLISIONS = 0.1
MIN_DURATION_FOR_COSMICS = 3600

def is_significant( rr_data, rr_run_class ):
  if 'special' in rr_data['oms_attributes']['hlt_key'].lower():
    return False
  elif 'collision' in rr_run_class.lower(): 
    if rr_data['oms_attributes']['recorded_lumi'] >= MIN_LUMI_FOR_COLLISIONS: return True
  elif 'cosmic' in rr_run_class.lower():
    if rr_data['oms_attributes']['duration'] >= MIN_DURATION_FOR_COSMICS: return True
  return False
  

COOKIES = None

def get_rr_run( run, log ):
  log.info("Get RR data for run %s ..." % run)

  url = 'https://cmsrunregistry.web.cern.ch/api/runs_filtered_ordered'
  request = '''
  { 
    "page" : 0,
    "page_size" : 100000,
    "sortings" : [],
    "filter" : {
      "run_number" : %s ,
      "rr_attributes.significant" : true
    }
  }
  ''' % ( run )
  
  global COOKIES
  try:
    if not COOKIES:
      COOKIES = cernrequests.get_sso_cookies(url, cert=(CERT, KEY), verify=False );

    try:
      response = requests.post(url, json=json.loads(request), cookies=COOKIES, verify=False)
    except:
      COOKIES = cernrequests.get_sso_cookies(url, cert=(CERT, KEY), verify=False );
      response = requests.post(url, json=json.loads(request), cookies=COOKIES, verify=False)

    try:
      result_json = json.loads(response.text)
      results_runs = result_json['runs']
      if not len(results_runs) : return { "rr_run_class" : "RR unknown", "rr_significant" : False } # no info about the run in RR
      rr_data = results_runs[0]
      # Logic to determine if run is significant for HDQM:
      # 1. If HLT key contains string "special", run is not significant
      # 2. For collision runs integrated luminosity has to be greater than 0.1 1/pb
      # 3. For cosmic runs duration has to be longer than 1 hour
      rr_run_class   = rr_data['rr_attributes']['class']
      rr_significant = is_significant( rr_data, rr_run_class )
      answer = { "rr_run_class" : rr_run_class, "rr_significant" : rr_significant }
      return answer
    except Exception as error_log:
      log.warning("Failed to get RR data for run %s ..." % run)
      log.warning('Error ... %s ' % error_log)
      log.warning('RR answer = "%s" ' % response.text)
      return 1
      
  except Exception as error_log:
    log.warning("Failed to get RR data for run %s ..." % run)
    log.warning('Error ... %s ' % error_log)
    return 1
  return None














