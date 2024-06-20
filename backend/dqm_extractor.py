#!/usr/bin/env python3
# P.S.~Mandrik, IHEP, 2022, https://github.com/pmandrik
# python3 -m pip install -r requirements.txt -t .python_packages/python3
# export PYTHONPATH=$PYTHONPATH:.python_packages/python3/
import os
import db
import re
import sys
import ROOT
import math
import logging
from logging.handlers import TimedRotatingFileHandler
import argparse
from configparser import RawConfigParser
from glob import glob
from collections import defaultdict

from extra import (
    TrendCfg,
    DQMFile,
    compare_configs,
    add_point_to_trend,
    get_plot_path,
    nostdout,
)

sys.path.append(os.path.dirname(os.path.realpath("./backend")))
from backend import oms_extractor
from backend import rr_extractor

from metrics import basic, fits, muon_metrics, L1T_metrics, hcal_metrics

LOGLEVEL = logging.DEBUG
LOGPATH = "./dqm_extractor.log"
CFGFILES = "backend/cfg/*/*.ini"
NLOGS = 10
GUIDATADIR = "/eos/cms/store/group/comm_dqm/DQMGUI_data"
GUIDATADIR = "/eos/cms/store/group/comm_dqm/DQMGUI_data/Run2022/MinimumBias/0003557xx/"
GUIDATADIR = "/eos/cms/store/group/comm_dqm/DQMGUI_data/*/*/*/"
GUIDATAPATTERN = "DQM_V*DQMIO.root"
PDPATTERN = re.compile("DQM_V\d+_R\d+__(.+__.+__.+)[.]root")  # PD inside the file name
VERSIONPATTERN = re.compile("(DQM_V)(\d+)(.+[.]root)")
RUNPATTERN = re.compile("DQM_V\d+_R0+(\d+)__.+[.]root")
PLOTNAMEPATTERN = re.compile("^[a-zA-Z0-9_+-]*$")
DQMGUI = "https://cmsweb.cern.ch/dqm/offline/"
METRICS_MAP = {
    "fits": fits,
    "basic": basic,
    "L1T_metrics": L1T_metrics,
    "muon_metrics": muon_metrics,
    "hcal_metrics": hcal_metrics,
}

logger = logging.getLogger(__name__)


def read_cfgs(cfg_files):
    logger.info(f"Reading configs from {len(cfg_files)} files.")
    check_dic = {}
    mes_set = set()
    trend_cfgs = []
    for cfg_file in cfg_files:
        logger.debug(f"Reading file {cfg_file}")
        try:
            parser = RawConfigParser()
            parser.read(cfg_file)
            subsystem = os.path.basename(os.path.dirname(cfg_file))
            if not subsystem:
                subsystem = "Unknown"

            for section in parser:
                if not section.startswith("plot:"):
                    if section != "DEFAULT":
                        logger.info(
                            "Invalid configuration section: %s:%s, skipping."
                            % (cfg_file, section)
                        )
                    continue
                if not PLOTNAMEPATTERN.match(section.lstrip("plot:")):
                    logger.info(
                        "Invalid plot name: '%s:%s' Plot names can contain only: [a-zA-Z0-9_+-]"
                        % (cfg_file, section.lstrip("plot:"))
                    )
                    continue

                trend = TrendCfg(cfg_file, section, parser[section], subsystem)

                pars = ["metric", "relativePath", "yTitle"]  # mandatory parameters
                for par in pars:
                    if par not in trend.data:
                        logger.info(
                            "Invalid configuration section: %s:%s, skipping."
                            % (cfg_file, section)
                        )
                        logger.info("Parameter not available %s" % par)
                        trend = None
                        break
                if not trend:
                    continue

                duplicate_trend = check_dic.get(subsystem + "@" + section, None)
                if duplicate_trend:
                    logger.info(
                        'Duplicate of plot name "%s" found in "%s" and in "%s". Skip'
                        % (section, cfg_file, duplicate_trend.cfg_path)
                    )
                    trend_cfgs.remove(duplicate_trend)
                    # print(section, cfg_file, duplicate_trend.cfg_path)
                    continue

                trend_cfgs += [trend]
                check_dic[subsystem + "@" + section] = trend
                mes_set.update(trend.GetMEs())

        except Exception as error_log:
            logger.info("Could not read %s, skipping..." % cfg_file)
            logger.info("Error ... %s " % error_log)

    return trend_cfgs, mes_set


def process_gui_root(file, trend_cfgs, mes):
    logger.info('Process "%s"' % file.path)

    ### get dataset & trends for type of root file name
    dataset = db.get_dataset(file.stream, file.reco_path)
    if not dataset:
        dataset = db.add_dataset(file.stream, file.reco_path)

    logger.info(
        'Process Dataset %s "%s" "%s"' % (dataset.id, dataset.stream, dataset.reco_path)
    )

    trends = db.get_trends(dataset)
    if not trends:
        db.add_trends(dataset, trend_cfgs)
        trends = db.get_trends(dataset)

    trends = sorted(trends, key=lambda x: x.config_id)

    ### read all MEs from root file
    logger.info('Extract MEs from "%s"' % file.path)
    try:
        tdirectory = ROOT.TFile.Open(file.path)
        if tdirectory == None:
            logger.warning("Unable to open file: '%s', skip" % file.path)
            return 1
    except Exception as error_log:
        logger.warning("Unable to read file: '%s', skip" % file.path)
        logger.warning("Error ... %s " % error_log)
        return 1

    me_dic = {}
    for me in mes:
        plot = tdirectory.Get(get_plot_path(me, file.run))
        if not plot:
            logger.debug('No MEs "%s" available in "%s"' % (me, file.path))
            continue
        me_dic[me] = plot
    logger.info("Available/Requested MEs = %s/%s" % (len(me_dic), len(mes)))

    ### calculate all trends based on MEs from root file
    logger.info('Calculating trends for "%s"' % file.path)
    processed_trends = []
    for trend_cfg, trend in zip(trend_cfgs, trends):
        metric_func = trend_cfg.metric_func
        if not metric_func:
            logger.info(
                "no metric for trend/cfg %s/%s, skip"
                % (trend_cfg.name, trend_cfg.cfg_path)
            )
            continue

        is_ok = True
        if trend_cfg.histo1_path:
            hist = me_dic.get(trend_cfg.histo1_path, None)
            if hist:
                metric_func.setOptionalHisto1(hist)
            else:
                is_ok = False

        if trend_cfg.histo2_path:
            hist = me_dic.get(trend_cfg.histo2_path, None)
            if hist:
                metric_func.setOptionalHisto2(hist)
            else:
                is_ok = False

        if trend_cfg.reference_path:
            hist = me_dic.get(trend_cfg.reference_path, None)
            if hist:
                metric_func.setReference(hist)
            else:
                is_ok = False

        main_hist = me_dic.get(trend_cfg.relative_path, None)
        if not main_hist:
            is_ok = False

        if not is_ok:
            logger.debug(
                "Unable to get an monitor element for trend/cfg %s/%s, skip"
                % (trend_cfg.name, trend_cfg.cfg_path)
            )
            continue

        # Calculate
        try:
            with nostdout():  # supress metrics stdout & stderr
                value, error = metric_func.calculate(main_hist)
        except Exception as error_log:
            logger.warning(
                "Unable to calculate the metric for trend/cfg %s/%s, skip"
                % (trend_cfg.name, trend_cfg.cfg_path)
            )
            logger.warning("Error ... %s " % error_log)
            continue

        if math.isinf(value):
            logger.warning(
                "Inf metric responce value for trend/cfg %s/%s, skip"
                % (trend_cfg.name, trend_cfg.cfg_path)
            )
            continue

        if math.isinf(error):
            logger.warning(
                "Inf metric responce error for trend/cfg %s/%s, skip"
                % (trend_cfg.name, trend_cfg.cfg_path)
            )
            continue

        # add new [run , value, error ] point to the trend
        # if we reprocessing the same run as in DB we updating points values
        add_point_to_trend(trend, dataset, trend_cfg, file.run, value, error)

        processed_trends += [trend]

    logger.info(
        "Processed/Requested Trends = %s/%s" % (len(processed_trends), len(trend_cfgs))
    )
    logger.info("Updating trends in the DB ...")
    db.session.commit()

    tdirectory.Close()
    return 0


if __name__ == "__main__":
    from dotenv import load_dotenv

    ### setup
    load_dotenv()
    parser = argparse.ArgumentParser(description="HDQM trend calculation.")
    log = logging.getLogger(__file__)
    logger.setLevel(LOGLEVEL)
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    if os.getenv("LOG_TO_FILE"):
        handler = TimedRotatingFileHandler(
            LOGPATH, when="h", interval=24, backupCount=int(NLOGS)
        )
        handler.setFormatter(formatter)
        handler.setLevel(LOGLEVEL)
        logger.addHandler(handler)

    handler2 = logging.StreamHandler(sys.stdout)
    handler2.setFormatter(formatter)
    handler2.setLevel(LOGLEVEL)
    logger.addHandler(handler2)

    logger.info("Start " + str(__file__))
    logger.info("Create %s log file" % LOGPATH)

    ### some metrics pop up canvases -_-
    ROOT.gROOT.SetBatch(True)

    ### get path to the db
    db_path = db.get_formatted_db_uri(
        username=os.environ.get("DB_USERNAME", "postgres"),
        password=os.environ.get("DB_PASSWORD", "postgres"),
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=os.environ.get("DB_PORT", 5432),
        db_name=os.environ.get("DB_NAME", "hdqm"),
    )
    db.create_session(db_path)

    ### read configs
    logger.info("Glob config files from %s" % CFGFILES)
    config_files = glob(CFGFILES)
    for cfg in config_files:
        # LOL?
        if cfg.count("/") != 3 or not cfg.startswith("backend/cfg/"):
            logger.info("Invalid configuration file: %s" % cfg)
            logger.info("Configuration files must come from here: cfg/*/*.ini")
            exit()
    logger.info("Count " + str(len(config_files)) + " cfg files")

    ### get Monitoring elements (MEs)
    logger.info("Read configuration files")
    trend_cfgs, mes = read_cfgs(config_files)
    logger.info("Count " + str(len(trend_cfgs)) + " Trends")
    logger.info("Count " + str(len(mes)) + " MEs")

    trend_dic = defaultdict(list)
    try:
        for item in trend_cfgs:
            subsystem = item.subsystem
            if not subsystem:
                subsystem = item.relative_path.split("/")[0]
                if not subsystem:
                    subsystem = item.relative_path.split("/")[1]
            trend_dic[subsystem] += [item]
    except Exception as error_log:
        logger.info("Could not count Trends per subsystem ...")
        logger.info("Error ... %s " % error_log)
        exit()

    mes_dic = defaultdict(list)
    try:
        check_list = list(mes)
        for item in check_list:
            subsystem = item.split("/")[0]
            if not subsystem:
                subsystem = item.split("/")[1]
            mes_dic[subsystem] += [item]
    except Exception as error_log:
        logger.info("Could not count MEs per subsystem ...")
        logger.info("Error ... %s " % error_log)
        exit()

    logger.info("--------------------Trends stat:")
    for key, val in trend_dic.items():
        logger.info(key + " : " + str(len(val)))

    logger.info("--------------------MEs stat:")
    for key, val in trend_dic.items():
        logger.info(key + " : " + str(len(val)))

    for key, val in mes_dic.items():
        if key in trend_dic:
            continue
        logger.info(key + " : " + str(None) + " " + str(len(val)))

    ### setup config metrics
    logger.info("Eval config metrics ...")
    metric_dic = defaultdict(int)
    for trend in trend_cfgs:
        try:
            metric = eval(trend.data["metric"], METRICS_MAP)
            trend.SetMetric(metric)
            metric_str = trend.data["metric"]
            metric_dic[metric_str.split("(")[0]] += 1
        except Exception as error_log:
            logger.info(
                'Could not setup metric "%s" for cfg "%s", trend "%s"'
                % (trend.data["metric"], trend.cfg_path, trend.name)
            )
            logger.info("Error ... %s " % error_log)
            exit()

    logger.info("-------------------- Metrics stat:")
    for key, val in metric_dic.items():
        logger.info(key + " : " + str(val))

    ### check trend configs in DB
    # - 1. add new configs or update old config
    #      we are not removing old configs or trends here, but they are not updated with new run information
    #      even if we updating the metric or reference in CFG used for calculation we do not change the DB trends
    logger.info("Get configs from the DB ...")
    try:
        db_cfgs = db.get_configs()
    except Exception as error_log:
        logger.info("Could not extract configs from the DB, exit")
        logger.info("Error ... %s " % error_log)
        exit()
    logger.info("Found %s configs in the DB " % len(db_cfgs))

    logger.info("Search for new configs to add or update ...")
    list_to_update = []
    list_to_add = []
    dic_overlap = {}
    for old_config in db_cfgs:
        dic_overlap[old_config.subsystem + "@" + old_config.name] = old_config
    for new_config in trend_cfgs:
        id = new_config.subsystem + "@" + new_config.name
        old_config = dic_overlap.get(id, None)
        if not old_config:
            list_to_add += [new_config]
            continue

        new_config.db_id = old_config.id

        if compare_configs(new_config, old_config):
            continue
        list_to_update += [[new_config, old_config]]

    logger.info(
        "Found %s new trend configs to add & %s configs to update in DB"
        % (len(list_to_add), len(list_to_update))
    )
    bad_configs_add = db.add_configs(list_to_add)
    bad_configs_update = db.update_configs(list_to_update)

    bad_configs = bad_configs_add + bad_configs_update
    if bad_configs:
        logger.warning(
            "Failed to add new trend configs (%s) or update configs (%s) to DB, abort"
            % ((bad_configs_add), (bad_configs_update))
        )
        exit()

    trend_cfgs_filtered = list(
        filter(lambda x: x.db_id, trend_cfgs)
    )  ## 100% sure we have db_id
    if len(trend_cfgs_filtered) != len(trend_cfgs):
        logger.warning(
            "Failed to add new trend configs or update configs, no ID returned by DB, abort"
        )
        exit()
    trend_cfgs = sorted(trend_cfgs_filtered, key=lambda x: x.db_id)  ## and sorted

    ### get known runs from the DB
    logger.info("Get known runs from the DB ...")
    db_runs = db.get_runs()
    db_runs_dic = {run.id: run for run in db_runs}
    logger.info("Found %s known runs ..." % len(db_runs))

    ### get list if root files
    root_files = []
    logger.info("The process was restarted, so, we need to check all new files")
    logger.info("Find all GUI ROOT files on EOS (several minutes ...)")

    import subprocess

    command = "find " + GUIDATADIR + " -name " + GUIDATAPATTERN
    logger.info('Execute "%s"' % command)
    try:
        output = subprocess.check_output(command, shell=True)
        output = output.decode("utf-8").split("\n")
        root_files = output
        if len(root_files) and not root_files[-1]:
            root_files.pop()  # remove last empty entries from find return
    except Exception as error_log:
        logger.info('find failed with error "%s"' % error_log)
        exit()

    logger.info("Find %s GUI files" % len(root_files))
    if not root_files:
        logger.info("No GUI files, check if EOS is down. Aborting.")
        exit()

    ### get good and latest dqm files
    logger.info("Filtering GUI files")

    dqm_files = defaultdict(dict)
    for path in root_files:
        name = os.path.basename(path)
        folder = os.path.dirname(path)
        version = int(name[len("DQM_V") : len("DQM_V") + 4])
        short_name = name[len("DQM_V") + 5 :]
        run = int(name[len("DQM_V0001_R") : len("DQM_V0001_R000355760")])
        stream = name.split("__")[1]
        reco_path = name.split("-")[1]

        new_element = DQMFile(
            path, folder, name, short_name, version, run, stream, reco_path
        )

        subdic = dqm_files[folder]
        if short_name in subdic:
            element = subdic[short_name]
            if element.version < version:
                element = new_element
        else:
            subdic[short_name] = new_element

    # print( list(dqm_files.values()) )
    # nfiles = len( sum( list(dqm_files.items()) ) )
    # logger.info('Number of GUI files after filtering %s' % nfiles )

    ### process files
    logger.info("Start extraction of MEs from files")
    good_files = 0
    for subdir, files in dqm_files.items():
        logger.info(
            'Process directory "%s" with %s files' % (subdir, len(files.values()))
        )
        files_tot = len(files.values())
        for n, file in enumerate(files.values()):
            logger.info("File number = %s/%s" % (n, files_tot))
            if db.check_gui_file(file):
                logger.info("Skip file already in the DB %s" % file.path)
                continue

            result = process_gui_root(file, trend_cfgs, mes)
            if not result:
                good_files += 1

            # add file as procecced to the DB
            db.add_gui_file(file)

            # if run is not known - update OMS and RR data
            db_run = db_runs_dic.get(file.run, None)
            if not db_run:
                db_run = db.add_run(file.run)
                db_runs_dic[file.run] = db_run

            if not db_run.oms_data:
                oms_data = oms_extractor.get_oms_run(db_run.id)
                if oms_data:
                    logger.info("Update oms run info for run %s" % db_run.id)
                    db_run.oms_data = str(oms_data)
                    db.session.commit()
                else:
                    logger.info("No OMS data for run %s" % db_run.id)

            if not db_run.rr_run_class:
                rr_data = rr_extractor.get_rr_run(file.run)
                if rr_data:
                    logger.info("Update RR run info for run %s" % db_run.id)
                    db_run.rr_run_class = str(rr_data["rr_run_class"])
                    db_run.rr_significant = bool(rr_data["rr_significant"])
                    db.session.commit()
                else:
                    logger.info("No RR data for run %s" % db_run.id)

    logger.info("Number of processed GUI files %s" % good_files)
