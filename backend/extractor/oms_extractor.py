#!/usr/bin/env python3
from __future__ import print_function

from sys import argv
from multiprocessing import Pool
from sqlalchemy.exc import IntegrityError

import json
import datetime
import requests
import argparse

import os, sys
# Insert parent dir to sys.path to import db_access and cern_sso
sys.path.insert(1, os.path.realpath(os.path.pardir))
import db_access
from cern_sso import get_cookies

CERT='../api/private/usercert.pem'
KEY='../api/private/userkey.pem'
CACERT='../api/etc/cern_cacert.pem'
PREMADE_COOKIE='../api/etc/oms_sso_cookie.txt'


def fetch(update, nproc):
  db_access.setup_db()

  all_runs = []
  extracted_runs = []

  session = db_access.get_session()
  try:
    print('Getting missing runs...')
    all_runs = list(session.execute('SELECT DISTINCT(run) FROM historic_data_points;'))
    all_runs = [x[0] for x in all_runs]
    extracted_runs = list(session.execute('SELECT DISTINCT(run) FROM oms_data_cache;'))
    extracted_runs = [x[0] for x in extracted_runs]
  finally:
    session.close()

  # Diff needs to be extracted!
  if update:
    diff = all_runs
  else:
    diff = [x for x in all_runs if x not in extracted_runs]

  print('Number of runs to be fetched: %s' % len(diff))

  db_access.dispose_engine()
  pool = Pool(nproc)
  pool.map(fetch_run, diff)
  print('Done.')


def fetch_run(run):
  print('Fetching run %s...' % run)
  db_access.dispose_engine()
  runs_url = 'https://cmsoms.cern.ch/agg/api/v1/runs?filter[run_number][eq]=%s&fields=start_time,end_time,b_field,energy,delivered_lumi,end_lumi,recorded_lumi,l1_key,hlt_key,l1_rate,hlt_physics_rate,duration,fill_number' % run

  try:
    cookies = get_sso_cookie(runs_url)
    oms_runs_json = json.loads(requests.get(runs_url, cookies=cookies, verify=CACERT).text)

    fills_url = 'https://cmsoms.cern.ch/agg/api/v1/fills?filter[fill_number][eq]=%s&fields=injection_scheme,era' % oms_runs_json['data'][0]['attributes']['fill_number']
    oms_fills_json = json.loads(requests.get(fills_url, cookies=cookies, verify=CACERT).text)
    
    # TODO: Change to prod url, add cookies and certificate
    dcs_collisions_lumis_url = '''https://vocms0183.cern.ch/agg/api/v1/lumisections?filter[run_number][eq]=%s
&filter[cms_active][eq]=true
&filter[bpix_ready][eq]=true
&filter[fpix_ready][eq]=true
&filter[tibtid_ready][eq]=true
&filter[tecm_ready][eq]=true
&filter[tecp_ready][eq]=true
&filter[tob_ready][eq]=true
&filter[ebm_ready][eq]=true
&filter[ebp_ready][eq]=true
&filter[eem_ready][eq]=true
&filter[eep_ready][eq]=true
&filter[esm_ready][eq]=true
&filter[esp_ready][eq]=true
&filter[hbhea_ready][eq]=true
&filter[hbheb_ready][eq]=true
&filter[hbhec_ready][eq]=true
&filter[hf_ready][eq]=true
&filter[ho_ready][eq]=true
&filter[dtm_ready][eq]=true
&filter[dtp_ready][eq]=true
&filter[dt0_ready][eq]=true
&filter[cscm_ready][eq]=true
&filter[cscp_ready][eq]=true
&filter[gem_ready][eq]=true
&fields=run_number
&page[limit]=1''' % run

    dcs_cosmics_lumis_url1 = '''https://vocms0183.cern.ch/agg/api/v1/lumisections
?filter[run_number][eq]=%s
&filter[dtm_ready][eq]=true
&filter[dtp_ready][eq]=true
&filter[dt0_ready][eq]=true
&fields=run_number
&page[limit]=1''' % run

    dcs_cosmics_lumis_url2 = '''https://vocms0183.cern.ch/agg/api/v1/lumisections
?filter[run_number][eq]=%s
&filter[cscm_ready][eq]=true
&filter[cscp_ready][eq]=true
&filter[gem_ready][eq]=true
&fields=run_number
&page[limit]=1''' % run

    is_dcs = False

    # For cosmics, we need to OR two terms. If first query if false, make a second one.
    if 'cosmic' in oms_runs_json['data'][0]['attributes']['hlt_key']:
      dcs_lumisections_json = json.loads(requests.get(dcs_cosmics_lumis_url1.replace('\n', ''), verify=False).text)
      if len(dcs_lumisections_json['data']):
        is_dcs = True
      else:
        dcs_lumisections_json = json.loads(requests.get(dcs_cosmics_lumis_url2.replace('\n', ''), verify=False).text)
        if len(dcs_lumisections_json['data']):
          is_dcs = True
    else:
      dcs_lumisections_json = json.loads(requests.get(dcs_collisions_lumis_url.replace('\n', ''), verify=False).text)
      if len(dcs_lumisections_json['data']):
        is_dcs = True

    # Add to cache
    session = db_access.get_session()
    try:
      oms_item = db_access.OMSDataCache(
        run = run,
        lumi = 0,
        start_time = datetime.datetime.strptime(oms_runs_json['data'][0]['attributes']['start_time'], "%Y-%m-%dT%H:%M:%SZ"),
        end_time = datetime.datetime.strptime(oms_runs_json['data'][0]['attributes']['end_time'], "%Y-%m-%dT%H:%M:%SZ"),
        b_field = oms_runs_json['data'][0]['attributes']['b_field'],
        energy = oms_runs_json['data'][0]['attributes']['energy'],
        delivered_lumi = oms_runs_json['data'][0]['attributes']['delivered_lumi'],
        end_lumi = oms_runs_json['data'][0]['attributes']['end_lumi'],
        recorded_lumi = oms_runs_json['data'][0]['attributes']['recorded_lumi'],
        l1_key = oms_runs_json['data'][0]['attributes']['l1_key'],
        l1_rate = oms_runs_json['data'][0]['attributes']['l1_rate'],
        hlt_key = oms_runs_json['data'][0]['attributes']['hlt_key'],
        hlt_physics_rate = oms_runs_json['data'][0]['attributes']['hlt_physics_rate'],
        duration = oms_runs_json['data'][0]['attributes']['duration'],
        fill_number = oms_runs_json['data'][0]['attributes']['fill_number'],
        is_dcs = is_dcs
      )

      try:
        oms_item.injection_scheme = oms_fills_json['data'][0]['attributes']['injection_scheme']
        oms_item.era = oms_fills_json['data'][0]['attributes']['era']
      except:
        oms_item.injection_scheme = None
        oms_item.era = None

      session.add(oms_item)
      session.commit()
    except IntegrityError as e:
      print('IntegrityError inserting OMS item: %s' % e)
      session.rollback()
      print('Updating...')
      
      try:
        oms_item_existing = session.query(db_access.OMSDataCache).filter(
          db_access.OMSDataCache.run == oms_item.run,
          db_access.OMSDataCache.lumi == oms_item.lumi
        ).one_or_none()

        if oms_item_existing:
          if isinstance(oms_item.start_time, datetime.datetime):
            oms_item_existing.start_time = oms_item.start_time
          else:
            oms_item_existing.start_time = datetime.datetime.strptime(oms_item.start_time, "%Y-%m-%dT%H:%M:%SZ")

          if isinstance(oms_item.end_time, datetime.datetime):
            oms_item_existing.end_time = oms_item.end_time
          else:
            oms_item_existing.end_time = datetime.datetime.strptime(oms_item.end_time, "%Y-%m-%dT%H:%M:%SZ")
          
          oms_item_existing.b_field = oms_item.b_field
          oms_item_existing.energy = oms_item.energy
          oms_item_existing.delivered_lumi = oms_item.delivered_lumi
          oms_item_existing.end_lumi = oms_item.end_lumi
          oms_item_existing.recorded_lumi = oms_item.recorded_lumi
          oms_item_existing.l1_key = oms_item.l1_key
          oms_item_existing.l1_rate = oms_item.l1_rate
          oms_item_existing.hlt_key = oms_item.hlt_key
          oms_item_existing.hlt_physics_rate = oms_item.hlt_physics_rate
          oms_item_existing.duration = oms_item.duration
          oms_item_existing.fill_number = oms_item.fill_number
          oms_item_existing.injection_scheme = oms_item.injection_scheme
          oms_item_existing.era = oms_item.era
          oms_item_existing.is_dcs = oms_item.is_dcs
          session.commit()
          print('Updated.')
      except Exception as e:
        print(e)
        session.rollback()
    except Exception as e:
      print(e)
      session.rollback()
    finally:
      session.close()
  except Exception as e:
    print(e)


def get_sso_cookie(url):
  if os.path.isfile(CERT) and os.path.isfile(KEY) and os.path.isfile(CACERT):
    return get_cookies(url, usercert=CERT, userkey=KEY, verify=CACERT)
  elif os.path.isfile(PREMADE_COOKIE):
    cookies = {}
    with open(PREMADE_COOKIE, 'r') as file:
      for line in file:
        fields = line.strip().split('\t')
        if len(fields) == 7:
          cookies[fields[5]] = fields[6]
    return cookies
  return None


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='HDQM data extraction from the OMS API.')
  parser.add_argument('-u', dest='update', action='store_true', help='If True, all runs will be updated. Otherwise only missing runs will be fetched. Default is False.')
  parser.add_argument('-j', dest='nproc', type=int, default=30, help='Number of processes to use in parallel.')
  args = parser.parse_args()

  update = args.update
  nproc = args.nproc
  fetch(update, nproc)
