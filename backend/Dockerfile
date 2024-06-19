###############################
# BASE IMAGE FOR OTHER STAGES
###############################

FROM rootproject/root:6.24.06-ubuntu20.04 as base

# The ROOT installed in the base image was compiled against python3 in ubuntu20.04 base image
# ROOT's team just installed the latest python version (3.8.x) at build time
#
# So in order to control python version (same as development version)
# we are going to install python 3.6.8 manually
#
# Note: Using this base image we can't change python's minor version
# since root is pre-compiled for python 3.8.x, i.e. we should compile root manually
# for a different python minor version if we need a different minor version
ARG PYTHON_VERSION=3.6.8

RUN wget https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz \
    && tar xzvf Python-${PYTHON_VERSION}.tgz \
    && rm Python-${PYTHON_VERSION}.tgz \
    && cd Python-${PYTHON_VERSION} \
    && ./configure \
    && make -j$(( $(getconf _NPROCESSORS_ONLN) - 2 )) \
    && make install \
    && cd .. \
    && rm -rf Python-${PYTHON_VERSION}

# PYTHONDONTWRITEBYTECODE: Prevents Python from writing pyc files to disc
# PYTHONUNBUFFERED: Prevents Python from buffering stdout and stderr
ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100

###############################
# RELEASE IMAGE
###############################

FROM base AS release

# This is to print directly to stdout instead of buffering output
ENV PYTHONUNBUFFERED 1

ARG UID=1000
ARG GID=1000

ENV USERNAME=app
ENV HOME=/home/$USERNAME
ENV APP_HOME=$HOME/backend

RUN mkdir -p $HOME
RUN mkdir $APP_HOME
RUN addgroup --system --gid $GID $USERNAME && adduser --system --ingroup $USERNAME --uid $UID $USERNAME

WORKDIR $APP_HOME

COPY requirements.txt $APP_HOME
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
#RUN pip3 install --no-cache /wheels/*

COPY backend $APP_HOME/backend
COPY run.sh $APP_HOME

RUN chown -R $USERNAME:$USERNAME $APP_HOME

USER $USERNAME

EXPOSE 5000

