# The default python installed in this release is 3.6.9
# Originally the application was design for 3.6.8, bumping the minor
# version is not a problem
FROM ubuntu:18.04

ENV LANG=C.UTF-8

ARG ROOT_BIN=root_v6.24.08.Linux-ubuntu18-x86_64-gcc7.5.tar.gz

WORKDIR /opt

RUN apt-get update -qq \
 && ln -sf /usr/share/zoneinfo/UTC /etc/localtime \
 && apt-get -y install wget \
 && wget https://raw.githubusercontent.com/root-project/root-docker/6.24.06-ubuntu20.04/ubuntu/packages \
 && apt-get -y install $(cat packages) python3-pip \
 && rm -rf /var/lib/apt/lists/* \
 && wget https://root.cern/download/${ROOT_BIN} \
 && tar -xzvf ${ROOT_BIN} \
 && rm -f ${ROOT_BIN} \
 && echo /opt/root/lib >> /etc/ld.so.conf \
 && ldconfig

ENV ROOTSYS /opt/root
ENV PATH $ROOTSYS/bin:$PATH
ENV PYTHONPATH $ROOTSYS/lib:$PYTHONPATH
ENV CLING_STANDARD_PCH none
ENV PYTHONNUNBUFFERED=1

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

COPY backend $APP_HOME/backend
COPY run.sh $APP_HOME

RUN chown -R $USERNAME:$USERNAME $APP_HOME

USER $USERNAME

EXPOSE 5000

