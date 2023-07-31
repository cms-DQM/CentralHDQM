import os
import sys
import re
import logging
from collections import defaultdict
from flask import Flask, jsonify, request, redirect
from flask_cors import CORS

logger = logging.getLogger(__name__)

app = Flask(__name__)

PDPATTERN = re.compile("DQM_V\d+_R\d+__(.+__.+__.+)[.]root")  # PD inside the file name
CORS(app)

from . import db

app.config["SQLALCHEMY_DATABASE_URI"] = db.get_formatted_db_uri(
    username=os.environ.get("DB_USERNAME", "postgres"),
    password=os.environ.get("DB_PASSWORD", "postgres"),
    host=os.environ.get("DB_HOST", "127.0.0.1"),
    port=os.environ.get("DB_PORT", 5432),
    db_name=os.environ.get("DB_NAME", "hdqm"),
)


@app.route("/api/data", methods=["GET"])
def get_data(json=True):
    if not json:
        pd = "MinimumBias"
        processing_string = "PromptReco"
        latest = 50
        subsystem = "SiStrips"
        from_run = 1
        to_run = 999999
        runs = None
        # runs = [ 355708, 355710, 355711 ]
        latest = 50
        trend_id = 0
    else:
        ### old HDQM code
        subsystem = request.args.get("subsystem")
        pd = request.args.get("pd")
        processing_string = request.args.get("processing_string")
        from_run = request.args.get("from_run", type=int)
        to_run = request.args.get("to_run", type=int)
        runs = request.args.get("runs")
        latest = request.args.get("latest", type=int)
        trend_id = request.args.get("trend_id", type=int)

        if subsystem == None:
            return jsonify({"message": "Please provide a subsystem parameter."}), 400

        if pd == None:
            return jsonify({"message": "Please provide a pd parameter."}), 400

        if processing_string == None:
            return (
                jsonify({"message": "Please provide a processing_string parameter."}),
                400,
            )

        modes = 0
        if from_run != None and to_run != None:
            modes += 1
        if latest != None:
            modes += 1
        if runs != None:
            modes += 1

        if modes > 1:
            return (
                jsonify(
                    {
                        "message": "The combination of parameters you provided is invalid."
                    }
                ),
                400,
            )

        if runs != None:
            try:
                runs = runs.split(",")
                runs = [int(x) for x in runs]
            except:
                return (
                    jsonify(
                        {
                            "message": "runs parameter is not valid. It has to be a comma separated list of integers."
                        }
                    ),
                    400,
                )

    ### runs
    if latest == None:
        latest = 50

    if runs:
        runs = db.session.query(db.Run).filter(db.Run.id.in_(runs)).all()
    elif from_run and to_run:
        runs = (
            db.session.query(db.Run)
            .where(db.Run.id >= from_run, db.Run.id <= to_run)
            .all()
        )
    else:
        runs = db.session.query(db.Run).order_by(db.Run.id.desc()).limit(latest).all()

    logger.debug(f"{[run.id for run in runs]}")
    ### datasets
    dataset = (
        db.session.query(db.Dataset)
        .where(db.Dataset.stream == pd, db.Dataset.reco_path == processing_string)
        .first()
    )

    ### trends & configs
    trends_and_configs = (
        db.session.query(db.Trend, db.Config)
        .where(db.Trend.dataset_id == dataset.id, db.Trend.subsystem == subsystem)
        .filter(db.Trend.config_id == db.Config.id)
        .all()
    )

    ### calc results
    result = []
    for trend, config in trends_and_configs:
        if trend_id:
            if trend.id != trend_id:
                continue

        points = eval(trend.points)
        trends_data = []

        for run in reversed(runs):
            if not run.rr_significant:
                continue

            point = points.get(run.id, None)
            if not point:
                continue

            dat = {
                "run": int(run.id),
                "value": float(point[0]),
                "error": float(point[1]),
                "oms_info": eval(run.oms_data),
            }
            trends_data.append(dat)

        # if not trends_data : continue

        result += [
            {
                "metadata": {
                    "y_title": config.y_title,
                    "plot_title": config.plot_title,
                    "name": config.name,
                    "subsystem": subsystem,
                    "pd": pd,  ### why we return what we requested ???
                    "processing_string": processing_string,
                    "relative_path": config.relative_path,
                    "histo1_path": config.histo1_path,
                    "histo2_path": config.histo2_path,
                    "reference_path": config.reference_path,
                    "trend_id": trend.id,
                },
                "trends": trends_data,
            }
        ]

    if json:
        return jsonify(result)
    return result


@app.route("/api/selection", methods=["GET"])
def get_selections(json=True):
    subsystems = db.session.query(db.Config.subsystem).distinct().all()
    datasets = (
        db.session.query(db.Dataset.id, db.Dataset.stream, db.Dataset.reco_path)
        .distinct()
        .all()
    )

    trends = (
        db.session.query(db.Trend.dataset_id, db.Trend.subsystem)
        .where(db.Trend.points != "{}")
        .all()
    )
    trends_dic = {}
    for trend in trends:
        trends_dic[str(trend.dataset_id) + "_" + str(trend.subsystem)] = 1

    obj = defaultdict(lambda: defaultdict(list))
    for s in subsystems:
        for d in datasets:
            key = str(d.id) + "_" + str(s.subsystem)
            if key not in trends_dic:
                continue
            obj[s.subsystem][d.stream].append(d.reco_path)

    if json:
        return jsonify(obj)
    return obj


@app.route("/api/plot_selection", methods=["GET"])
def plot_selection(json=True):
    # try:
    subsystems = db.session.query(db.Config.subsystem).distinct().all()
    datasets = (
        db.session.query(db.Dataset.id, db.Dataset.stream, db.Dataset.reco_path)
        .distinct()
        .all()
    )
    configs = db.session.query(db.Config.id, db.Config.name).all()

    trends = (
        db.session.query(db.Trend.dataset_id, db.Trend.subsystem, db.Trend.config_id)
        .where(db.Trend.points != "{}")
        .all()
    )
    trends_dic = defaultdict(dict)
    for trend in trends:
        trends_dic[str(trend.dataset_id) + "_" + str(trend.subsystem)][
            trend.config_id
        ] = trend.id

    obj = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for s in subsystems:
        for d in datasets:
            key = str(d.id) + "_" + str(s.subsystem)
            if key not in trends_dic:
                continue

            trend_n_cfg = trends_dic[key]
            plots = [
                {"name": cfg.name, "id": trend_n_cfg[cfg.id]}
                for cfg in configs
                if cfg.id in trend_n_cfg
            ]

            obj[s.subsystem][d.stream][d.reco_path] = plots

    if json:
        return jsonify(obj)
    return obj


@app.route("/api/runs", methods=["GET"])
def get_runs(json=True):
    db.create_session(db_path)
    runs = [r.id for r in db.session.query(db.Run.id).order_by(db.Run.id.asc())]
    if json:
        return jsonify(runs)
    return runs


###


@app.route("/api/expand_url", methods=["GET"])
def expand_url():
    valid_url_types = {
        "main_gui_url": "relative_path",
        "main_image_url": "relative_path",
        "optional1_gui_url": "histo1_path",
        "optional1_image_url": "histo1_path",
        "optional2_gui_url": "histo2_path",
        "optional2_image_url": "histo2_path",
        "reference_gui_url": "reference_path",
        "reference_image_url": "reference_path",
    }

    url_type = request.args.get("url_type")
    run = request.args.get("run", type=int)
    trend_id = request.args.get("trend_id", type=str)
    subsystem = request.args.get("subsystem", type=str)
    pd = request.args.get("pd", type=str)
    ps = request.args.get("ps", type=str)

    if run == None:
        return jsonify({"message": "Please provide a run parameter."}), 400

    if trend_id == None:
        return jsonify({"message": "Please provide a trend_id parameter."}), 400

    if subsystem == None:
        return jsonify({"message": "Please provide a subsystem parameter."}), 400

    if pd == None:
        return jsonify({"message": "Please provide a pd parameter."}), 400

    if ps == None:
        return jsonify({"message": "Please provide a ps parameter."}), 400

    if url_type not in valid_url_types:
        return (
            jsonify(
                {
                    "message": "Please provide a valid url_type parameter. Accepted values are: %s"
                    % ",".join(valid_url_types)
                }
            ),
            400,
        )

    trends_and_configs = (
        db.session.query(db.Trend, db.Config)
        .where(db.Trend.id == trend_id)
        .filter(db.Trend.config_id == db.Config.id)
        .first()
    )
    if not config:
        return (
            jsonify(
                {
                    "message": "Can not find config with subsystem, series_id = '"
                    + str(subsystem)
                    + "', '"
                    + str(series_id)
                    + "'"
                }
            ),
            400,
        )

    getter = valid_url_types[url_type]
    me_path = getattr(config, getter)
    try:  # if not me_path :
        plot_folder = "/".join(me_path.split("/")[:-1])
    except:
        return jsonify({"message": "Requested URL type is not found."}), 404

    # where reco_path = 'PromptReco' and stream = 'Cosmics' and run = '335614';
    gui_file = (
        db.session.query(db.GUIFile)
        .where(
            db.GUIFile.reco_path == ps,
            db.GUIFile.stream == pd,
            db.GUIFile.run == str(run),
        )
        .first()
    )
    if not gui_file:
        return (
            jsonify(
                {
                    "message": "Can not find GUIFile with reco_path, stream, run = '"
                    + str(reco_path)
                    + "', '"
                    + str(stream)
                    + "', '"
                    + str(run)
                    + "'"
                }
            ),
            400,
        )

    dataset = ""
    pd_match = PDPATTERN.findall(gui_file.path)
    if len(pd_match):
        dataset = "/" + pd_match[0].replace("__", "/")
    else:
        return (
            jsonify(
                {"message": "Can find dataset in eos file path '" + gui_file.path + "'"}
            ),
            400,
        )

    DQMGUI = "https://cmsweb.cern.ch/dqm/offline/"
    gui_url = (
        "%sstart?runnr=%s;dataset=%s;workspace=Everything;root=%s;focus=%s;zoom=yes;"
        % (DQMGUI, run, dataset, plot_folder, me_path)
    )
    image_url = "%splotfairy/archive/%s%s/%s?v=1510330581101995531;w=1906;h=933" % (
        DQMGUI,
        run,
        dataset,
        me_path,
    )

    url = gui_url
    if "image" in url_type:
        url = image_url

    url = url.replace("+", "%2B")
    return redirect(url, code=302)
    ### return jsonify({'message': 'Error getting the url from the DB.'}), 500


###
@app.route("/api/")
def index():
    return jsonify("HDQM REST API")


def do_tests():
    print("HDQM API do some tests ... ")
    print("Subsystems ... ")
    subsystems = get_selections(False)
    print(subsystems)
    print("Runs ... ")
    runs = get_runs(False)
    print(runs)
    print("Data ... ")
    data = get_data(False)
    print(data)
    pass


def create_app():
    """
    Entrypoint
    """
    # do_tests()
    # exit()
    from dotenv import load_dotenv

    load_dotenv()

    db_path = db.get_formatted_db_uri(
        username=os.environ.get("DB_USERNAME", "postgres"),
        password=os.environ.get("DB_PASSWORD", "postgres"),
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=os.environ.get("DB_PORT", 5432),
        db_name=os.environ.get("DB_NAME", "hdqm"),
    )
    db.create_session(db_path)
    return app
