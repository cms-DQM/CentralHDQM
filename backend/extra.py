# P.S.~Mandrik, IHEP, 2022, https://github.com/pmandrik

import sys, os
import contextlib


### DQM classes
class TrendCfg:
    def __init__(self, cfg_path, name, data, subsystem):
        self.cfg_path = cfg_path
        self.name = name
        self.data = data
        self.subsystem = subsystem
        self.y_title = data.get("yTitle", None)
        self.plot_title = data.get("plotTitle", None)
        self.relative_path = data.get("relativePath", None)
        self.histo1_path = data.get("histo1Path", None)
        self.histo2_path = data.get("histo2Path", None)
        self.reference_path = data.get("reference", None)
        self.metric = data.get("metric", None)
        self.threshold = data.get("threshold", None)
        self.metric_func = None
        self.db_id = None

    def SetMetric(self, metric_func):
        self.metric_func = metric_func
        if self.threshold:
            self.metric_func.setThreshold(int(self.threshold))

    def GetMEs(self):
        answer = [
            self.relative_path,
            self.histo1_path,
            self.histo2_path,
            self.reference_path,
        ]
        return [x for x in answer if x]


class DQMFile:
    def __init__(self, path, folder, name, short_name, version, run, stream, reco_path):
        self.path = path
        self.folder = folder
        self.name = name
        self.short_name = short_name
        self.version = version
        self.run = run
        self.stream = stream
        self.reco_path = reco_path


### no STDOUT & STDERR hack
class DummyFile(object):
    def write(self, x):
        pass


@contextlib.contextmanager
def nostdout():
    save_stdout = sys.stdout
    save_stderr = sys.stderr
    sys.stdout = DummyFile()
    sys.stderr = DummyFile()
    yield
    sys.stdout = save_stdout
    sys.stderr = save_stderr


### compare config in DB and text file
def compare_configs(new_config, old_config):
    attributes = [
        "y_title",
        "plot_title",
        "metric",
        "relative_path",
        "histo1_path",
        "histo2_path",
        "reference_path",
        "threshold",
    ]
    for attr in attributes:
        # print( attr, getattr(new_config, attr), getattr(old_config, attr) )
        if getattr(new_config, attr) != getattr(old_config, attr):
            print(
                new_config.cfg_path,
                type(getattr(new_config, attr)),
                type(getattr(old_config, attr)),
            )
            print(attr, getattr(new_config, attr), getattr(old_config, attr))
            return 0
    return 1


### transform path defined in CFG to actual path in ROOT file
def get_plot_path(path, run):
    parts = path.split("/")
    return str(
        "DQMData/Run %s/%s/Run summary/%s" % (run, parts[0], "/".join(parts[1:]))
    )


### update trends informations with data points
import bisect


def add_point_to_trend(trend, dataset, trend_cfg, run, value, error, log):
    trend.points.replace("inf", "0")
    try:
        points = eval(trend.points)
        # log.info('Run %s duplicate point in trend "%s" dataset "%s" "%s" config "%s" "%s"' % (str(run), trend.subsystem, dataset.stream, dataset.reco_path, trend_cfg.name, trend_cfg.plot_title) )
        points[run] = [value, error]
    except Exception as error_log:
        log.info(
            "Failed to add point to trend %s/%s" % (trend_cfg.name, trend_cfg.cfg_path)
        )
        log.info("Trend points %s" % (str(trend.points)))
        log.info("Error ... %s " % error_log)
        return False
    trend.points = str(points)
    return True
