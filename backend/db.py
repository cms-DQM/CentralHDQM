# P.S.~Mandrik, IHEP, 2022, https://github.com/pmandrik

import os
import logging
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import ProgrammingError
from sqlalchemy import (
    Text,
    Column,
    String,
    Integer,
    Float,
    DateTime,
    Boolean,
    ForeignKey,
    Enum,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import select

logger = logging.getLogger(__name__)

Base = declarative_base()

# SQLite will be used if no production DB credentials will be found
session = None
engine = None


def get_formatted_db_uri(
    username: str = "postgres",
    password: str = "postgres",
    host: str = "postgres",
    port: int = 5432,
    db_name="postgres",
) -> str:
    """
    Helper function to format the DB URI for SQLAclhemy
    """
    return f"postgresql://{username}:{password}@{host}:{port}/{db_name}"


def create_session(db_string=None):
    global session
    global engine

    if not db_string:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        db_string = "sqlite:///" + os.path.join(dir_path, "hdqm_v3.db")
        engine = sqlalchemy.create_engine(db_string + "?check_same_thread=False")
        Session = sessionmaker(bind=engine)
    else:
        engine = sqlalchemy.create_engine(db_string)
        Session = sessionmaker(bind=engine)

    session = Session()


# ~10k Files
# ~1k  MEs
# ~1k  Trends
# 20 runs per day
# => can be slow to update but rather fast to read data from DB


##################################### Tables
# table to store run data and status
class Run(Base):
    __tablename__ = "Runs"
    id = Column(Integer, primary_key=True, nullable=False)
    rr_run_class = Column(Text)
    rr_significant = Column(Boolean)
    oms_data = Column(Text)


class GUIFile(Base):
    __tablename__ = "GUIFiles"
    path = Column(String, primary_key=True, nullable=False)
    short_name = Column(String)
    version = Column(String)
    run = Column(String)
    stream = Column(String)
    reco_path = Column(String)


# table with dataset atribute values
# per dataset we have several trends (to be shown as plots)
class Dataset(Base):
    __tablename__ = "Datasets"
    id = Column(Integer, primary_key=True, nullable=False)
    stream = Column(String)
    reco_path = Column(String)
    trends = relationship("Trend")


# table with configs data
class Config(Base):
    __tablename__ = "Configs"
    id = Column(Integer, primary_key=True, nullable=False)
    subsystem = Column(String)
    name = Column(String)
    # used to plot
    y_title = Column(String)
    plot_title = Column(String)
    # used to calculate
    metric = Column(String)
    relative_path = Column(String)
    histo1_path = Column(String)
    histo2_path = Column(String)
    reference_path = Column(String)
    threshold = Column(String)
    # trends
    trends = relationship("Trend")


# table with trends, value+error point per run and metadata
class Trend(Base):
    __tablename__ = "Trends"
    id = Column(Integer, primary_key=True, nullable=False)
    subsystem = Column(String)
    dataset_id = Column(Integer, ForeignKey("Datasets.id"))
    config_id = Column(Integer, ForeignKey("Configs.id"))
    points = Column(Text)


##################################### Helping functions
def get_runs():
    runs = session.query(Run).all()
    return runs


def add_run(run_number):
    logger.info('Add new run "%s" to the DB ...' % (run_number))
    run = Run(id=run_number)
    session.add(run)
    session.commit()
    logger.info("Add new run ... ok")
    return run


def get_configs():
    configs = session.query(Config).all()
    return configs


def add_configs(configs):
    logger.info("Add new configs to the DB ...")

    try:
        configs_to_add = []
        for config in configs:
            db_config = Config()
            attributes = [
                "subsystem",
                "name",
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
                setattr(db_config, attr, getattr(config, attr))
            configs_to_add += [db_config]
        session.bulk_save_objects(configs_to_add, return_defaults=True)  # to have an id
        for c1, c2 in zip(configs, configs_to_add):
            c1.db_id = c2.id
        # apply changes
        session.commit()
    except Exception as error_log:
        logger.warning(
            "failed to add config to the DB %s/%s, skip"
            % (config.name, config.cfg_path)
        )
        logger.warning("Error ... %s " % error_log)
        return 1

    return 0


def update_configs(configs):
    logger.info("Update configs in the DB ...")
    try:
        for config_new, config_old in configs:
            attributes = [
                "subsystem",
                "name",
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
                setattr(config_old, attr, getattr(config_new, attr))
        # apply changes
        session.commit()
    except Exception as error_log:
        logger.warning(
            "failed to add config to the DB %s/%s, skip"
            % (config.name, config.cfg_path)
        )
        logger.warning("Error ... %s " % error_log)
        return 1

    return 0


def get_dataset(stream, reco_path):
    dataset = (
        session.query(Dataset)
        .where(Dataset.stream == stream, Dataset.reco_path == reco_path)
        .first()
    )
    return dataset


def get_trends(dataset):
    trends = session.query(Trend).where(Trend.dataset_id == dataset.id).all()
    return trends


def add_dataset(stream, reco_path):
    logger.info('Add new dataset ("%s", "%s") to the DB ...' % (stream, reco_path))
    dataset = Dataset()
    dataset.stream = stream
    dataset.reco_path = reco_path
    session.add(dataset)
    session.commit()
    logger.info("Add new dataset ... ok")
    return dataset


def add_trends(dataset, trend_cfgs):
    logger.info(
        'Add new trends of dataset ("%s", "%s") to the DB ...'
        % (dataset.stream, dataset.reco_path)
    )
    trends_to_add = []
    for config in trend_cfgs:
        trend = Trend()
        trend.subsystem = config.subsystem
        trend.dataset_id = dataset.id
        trend.config_id = config.db_id
        trend.points = "{}"
        trends_to_add += [trend]
    session.bulk_save_objects(trends_to_add)
    session.commit()
    logger.info("Add new trends ... ok")


def add_gui_file(file):
    logger.info('Add processed gui file ("%s") to the DB ...' % (file.path))
    f = GUIFile(path=file.path)
    attributes = ["short_name", "version", "run", "stream", "reco_path"]
    for attr in attributes:
        setattr(f, attr, getattr(file, attr))
    session.add(f)
    session.commit()
    logger.info("Add gui file ... ok")


def check_gui_file(file):
    files = session.query(GUIFile).where(GUIFile.path == file.path).first()
    return files


##################################### DB API


# setup DB
def setup_db(db_path):
    db_path = "/".join(db_path.split("/")[:-1]) + "/postgres"
    try:
        engine = sqlalchemy.create_engine(db_path)
        conn = engine.connect()
        conn.execute("COMMIT")
        conn.execute(f"CREATE DATABASE {os.getenv('DB_NAME')}")
        conn.close()
        engine.dispose()
    except ProgrammingError as err:
        if "already exists" in str(err):
            print("Database already exists")
        else:
            raise err
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    ### get path to the db
    from dotenv import load_dotenv

    load_dotenv()
    db_path = get_formatted_db_uri(
        username=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        db_name=os.getenv("DB_NAME"),
    )
    create_session(db_path)
    setup_db(db_path)
