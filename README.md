# Table of contents

- [Table of contents](#table-of-contents)
- [Central Historic DQM application for CMS detector](#central-historic-dqm-application-for-cms-detector)
- [Usage instructions](#usage-instructions)
  * [How to run locally](#how-to-run-locally)
    + [New ssh connection](#new-ssh-connection)
  * [Main HDQM commands explained](#main-hdqm-commands-explained)
    + [`hdqmextract.py`](#-hdqmextractpy-)
    + [`calculate.py`](#-calculatepy-)
    + [Other tools](#other-tools)
    + [Summary](#summary)
  * [How to add new plots](#how-to-add-new-plots)
    + [Backend configuration](#backend-configuration)
    + [Frontend configuration](#frontend-configuration)
    + [Adding new metrics](#adding-new-metrics)
  * [Web application usage](#web-application-usage)
- [API documentation](#api-documentation)
  * [Endpoints](#endpoints)
    + [`/api/data`](#--api-data-)
    + [`/api/selection`](#--api-selection-)
    + [`/api/plot_selection`](#--api-plot-selection-)
    + [`/api/runs`](#--api-runs-)
    + [`/api/expand_url`](#--api-expand-url-)
- [Administration instructions](#administration-instructions)
  * [API local setup instructions](#api-local-setup-instructions)
    + [Instructions on how to retrieve the certificate and the key:](#instructions-on-how-to-retrieve-the-certificate-and-the-key-)
  * [Daily extraction](#daily-extraction)
    + [EOS access](#eos-access)
  * [How to update](#how-to-update)
    + [How to rollback to the old version](#how-to-rollback-to-the-old-version)

# Central Historic DQM application for CMS detector

A tool to display trends of CMS DQM quantities over long periods of time.  
The web application is available here: https://cms-hdqm.web.cern.ch  
The code is running on a `vocms0231` machine.

# Usage instructions

## How to run locally

The following instruction are completely copy-pastable. This will start a complete HDQM stack on your local (lxplus) environment. This is perfect for testing new plots before adding them. Instructions are are made for bash shell.

``` bash
# Enter bash
bash
# You have to change the username. From this point, all instruction can be copy pasted without modifications.
ssh -L 8000:localhost:8000 -L 8080:localhost:5000 <YOUR_USER_NAME>@lxplus7.cern.ch
/bin/bash
mkdir -p /tmp/$USER/hdqm
cd /tmp/$USER/hdqm/

git clone https://github.com/cms-dqm/CentralHDQM
cd CentralHDQM/

# Get an SSO to access OMS and RR APIs. This has to be done before cmsenv script
# First check if we are the owner of the folder where we'll be puting the cookie
# Cookie for  Run Registry:
cern-get-sso-cookie --cert ~/private/usercert.pem --key ~/private/userkey.pem -u https://cmsrunregistry.web.cern.ch/api/runs_filtered_ordered -o backend/api/etc/rr_sso_cookie.txt

cd backend/
# Need to add client secret backend/.env file - ask DQM conveners to provide it.
nano .env

# This will give us cern-get-sso-cookie -u https://cmsoms.cern.ch/agg/api/v1/runs -o backend/api/etc/oms_sso_cookie.txta CMSSW environment
source cmsenv

# Add python dependencies
python3 -m pip install -r requirements.txt -t .python_packages/python3
python -m pip install -r requirements.txt -t .python_packages/python2

export PYTHONPATH="${PYTHONPATH}:$(pwd)/.python_packages/python2"

cd extractor/

# Extract few DQM histograms. Using only one process because we are on SQLite
./hdqmextract.py -c cfg/PixelPhase1/trendPlotsPixelPhase1_tracks.ini -r 324997 324998 324999 325000 325001 325022 325057 325097 325098 325099 -j 1

# Calculate HDQM values from DQM histograms stored in the DB
./calculate.py -c cfg/PixelPhase1/trendPlotsPixelPhase1_tracks.ini -r 324997 324998 324999 325000 325001 325022 325057 325097 325098 325099 -j 1

# Get the OMS and RR data about the runs
./oms_extractor.py
./rr_extractor.py

cd ../api/
# Run the API
./run.sh &>/dev/null &

cd ../../frontend/
# Use local API instead of the production one
sed -i 's/\/api/http:\/\/localhost:8080\/api/g' js/config.js
# Run the static file server
python3 -m http.server 8000 &>/dev/null &

# Run this to find pids of running servers to kill them:
# ps awwx | grep python
```

That's it! Now visit http://localhost:8000/ on your browser.

### New ssh connection

If you have already successfully executed the instructions above and you want to keep working on the same deployment with new `ssh` connection, please follow the instructions bellow:

``` bash
/bin/bash
cd /tmp/$USER/hdqm/CentralHDQM/

cern-get-sso-cookie --cert ~/private/usercert.pem --key ~/private/userkey.pem -u https://cmsrunregistry.web.cern.ch/api/runs_filtered_ordered -o backend/api/etc/rr_sso_cookie.txt

cd backend/
source cmsenv

export PYTHONPATH="${PYTHONPATH}:$(pwd)/.python_packages/python2"

cd api/
./run.sh &>/dev/null &

cd ../../frontend/
python3 -m http.server 8000 &>/dev/null &
```

## Main HDQM commands explained

Main HDQM commands are the following:

1. `hdqmextract.py`
2. `calculate.py`

### `hdqmextract.py`

This tool is responsible for extracting DQM monitor elements from ROOT files and storing them as binary data in the database. This is separated from HDQM value calculation to ensure that values can be recalculated quickly, without relying on a file system every time.

| Argument | Long name | Default value                                             | Description                                                                                                                                                                                                                                                                                       |
|----------|-----------|-----------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| -r       | runs      | None                                                      | A list of runs. Only MEs containing info of these runs will be extracted and saved. By default, MEs from all runs available in the given DQM files will be extracted.                                                                                                                             |
| -c       | config    | cfg/\*/\*.ini                                               | A list of `.ini` configuration files to be used. A pattern of a config file location is this: `cfg/<SUBSYSTEM_NAME>/<ARBITRARY_NAME>.ini`. This pattern must be followed without any additional folders in between. If a subsystem folder is missing, it can be created.                          |
| -f       | files     | EOS dir | A list of DQM files to be used. This is very useful if you want to do HDQM on your custom set of DQM files. Files still need to follow DQM file naming conventions (must contain a run and a dataset name). Also this can be used to run HDQM on a subset of all DQM ROOT files available in EOS. |
| -j       | nprocs    | 50                                                        | Integer value indicating how many processes to use. **When running locally (on SQLite) this has to be 1** because SQLite doesn't support multiple connections writing to the DB.                                                                                                                  |

Default EOS directory for `-f` argument is this: `/eos/cms/store/group/comm_dqm/DQMGUI_data/*/*/*/DQM*.root`

### `calculate.py`

This tool is responsible for reducing every DQM monitor element found in the database to a value that will be plotted, based on user defined metrics.

| Argument | Long name | Default value | Description                                                                                                                                                                                                                                                              |
|----------|-----------|---------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| -r       | runs      | None          | A list of runs. HDQM values will be calculated only for MEs containing info of these runs. By default, HDQM will be calculated for all MEs that were extracted.                                                                                                          |
| -c       | config    | cfg/\*/\*.ini   | A list of `.ini` configuration files to be used. A pattern of a config file location is this: `cfg/<SUBSYSTEM_NAME>/<ARBITRARY_NAME>.ini`. This pattern must be followed without any additional folders in between. If a subsystem folder is missing, it can be created. |
| -j       | nprocs    | 50            | Integer value indicating how many processes to use. **When running locally (on SQLite) this has to be 1** because SQLite doesn't support multiple connections writing to the DB.                                                                                         |

### Other tools

When new runs appear in the database, OMS and RR APIs need to be queried to find out if new runs need to be filtered out or not. For this, the following tools need to be executed, in this specific order:

``` bash
./oms_extractor.py
./rr_extractor.py
```

If a big chuck of new data was recently extracted, there is a tool to prewarm the database for initial queries be fast:

`./db_prewarm.py`

### Summary

To summarize, by default HDQM will be done on all data available in EOS and all configuration files available in `cfg/`. The parameters to HDQM tools can be helpful to limit this scope and only extract the required subset of the data or your own data altogether.

## How to add new plots

In order to add new plots to HDQM, you have to provide two layers of configuration:  
1. backend configuration
2. frontend configuration

Configuration is all in code and in order to add new plots you have to make a pull request against this repo: https://github.com/cms-DQM/CentralHDQM

### Backend configuration

Backend is configured with `.ini` files that describe what monitor elements should be taken from the DQM `.root` files and how the value from the should be extracted for plotting.  
These files are placed here, in a corresponding subsystem directory: `backend/extractor/cfg/<subsystem>`. This directory structure has to be preserved in order for the tool to work. If subsystem doesn't exist, a folder for it can be created.

Let's take a look at an example:

``` ini
[plot:Ntracks_Pixel]
metric = basic.BinCount(2)
relativePath = PixelPhase1/Tracks/ntracks
plotTitle = Pixel number of tracks
yTitle = Number of Tracks in Pixel
```

That's all it takes to tell HDQM how to plot a DQM quantity over time. Let's break this down line by line.

* The first line describes an ID of a plot that is unique per subsystem. This ID will be used to refer to this plot later on. *This field is required*.
* **metric** property tells the tool what function needs to be called to reduce a DQM histogram to a single value that will be plotted. Think of this as of a constructor call of a Python class. Classes that can be used are defined here: `backend/extractor/metrics/`. If necessary, new python classes could be added. New classes have to provide a constructor with as many arguments as it's required to be referred to from the configuration and a `calculate(self, histo)` method that will be called by the backend. This function has to return a tuple of two values `(value, error)`. For more details, refer to *Adding new metric* section bellow. *This field is required*.
* **relativePath** is a path of a monitor element in a legacy DQM root file that a metric should be applied to. In case a path of a monitor element changed, you can provide multiple, space separated paths here. ME that is found the first will be used. *This field is required*.
* **plotTitle** is a title of a plot that will be displayed in a web application. This value can contain spaces as it only has to be human readable. If this field is not provided, yTitle will be used instead. *This field is not required*.
* **yTitle** is a title of y axis. It is usually used to display the units used in a plot. *This field is required*.

Those were the main properties, however there are other less common ones:

``` ini
histo1Path = PixelPhase1/Phase1_MechanicalView/PXBarrel/num_clusters_PXLayer_2
histo2Path = PixelPhase1/Phase1_MechanicalView/PXBarrel/size_PXLayer_2
threshold = 50
```

* Sometimes, a value of a point in a trend depends on more than one DQM histogram. In such cases **histo1Path** and **histo2Path** could be used to define the paths of the other histograms. *These fields are not required*.
* **threshold** was used previously to define a minimum number of entries for a histogram to be taken into a trend. Now, this is no longer used, however this value can be wired in your custom Python extraction class. *This field is not required*.

### Frontend configuration

In a frontend configuration you can define what is called **display groups**. Display groups define a list of related plots that will be displayed together in a web application, as an overlay.  
The configuration is located here: `frontend/js/displayConfig.js`. All fields here are required!

Let's take a look at an example:

``` js
{
  name: "an_id_of_a_display_group",
  plot_title: "Nice, readable title of a group",
  y_title: "Units of all series in a group",
  subsystem: "<Subsystem>",
  correlation: false,
  series: ["plot1_ID", "plot2_ID"],
}
```

Let's break this down line by line.

* **name** is an ID of a display group. It has to be unique within all display groups and regular plots within a subsystem.
* **plot_title** is a title of a grouped plot that will be displayed in a web application. 
* **y_title** is a title of y axis of a grouped plot. It is usually used to display the units used in a plot.
* **subsystem** is the name of the subsystem. It has to match exactly the name of the folder where backend configuration files came from (`backend/extractor/cfg/<subsystem>`).
* **correlation** is a boolean value defining if the plot should be displayed in a correlation mode. This can be `true` only when there are exactly 2 series in a display group.
* **series** is an array if plot ID from backend configuration that will appear in a display group.

### Adding new metrics

In section we will look at how to add new metrics to the HDQM.

Create a new python file inside metrics directory:
``` bash
vim backend/extractor/metrics/sampleMetrics.py
```

Import `BasicMetric` and define your new class:
``` py
from basic import BaseMetric

class Mean(BaseMetric):
  def calculate(self, histo):
    return (histo.GetMean(), histo.GetMeanError())
```

`histo` is a full ROOT histogram, which, luckily, already provides getting its mean, so our implementation is very simple. **Keep in mind that you always have to return a tuple of 2 numbers: value and error!**

Also, **all metrics have to inherit `BasicMetric` and implement `calculate(self, histo)` method**

Now, add the new metric to the calculation script:

``` bash
vim backend/extractor/calculate.py
```

Import it:

``` python
from metrics import sampleMetrics
```

And add the new metric to the (already defined) `METRICS_MAP`:

``` python
METRICS_MAP = {'fits': fits, 'basic': basic, 'L1T_metrics': L1T_metrics, 'muon_metrics': muon_metrics, 'sampleMetrics': sampleMetrics}
```

Now, your newly added metric can be used in the `.ini` file like this:

``` ini
metric = sampleMetrics.Mean()
```

In this definition we are essentially calling a constructor of `sampleMetrics.Mean`. If you need to pass parameters to the metric, you can define a constructor and pass parameters from the configuration files. For example:

``` py
from basic import BaseMetric

class BinCount(BaseMetric):
  def __init__(self,  binNr):
    self.__binNr = binNr
  def calculate(self, histo):    
    return (histo.GetBinContent(self.__binNr), 0)
```

This will be a trend of counts of first bin:

``` ini
metric = sampleMetrics.BinCount(1)
```

## Web application usage 

In a web application, user has to select the data first by selecting a **subsystem**, **primary dataset** and a **processing string** at a very top of the page and all plots present in selected data will be displayed.

Runs can be filtered in one of the following ways:

* Latest N runs
* Run range
* Comma separated list of runs
* Golden JSON file

By clicking **Options** button, a display mode of the plots can be chosen. Available display modes are:

* Scatter plot
* Bin width proportional to run duration
* Bin width proportional to integrated luminosity
* Datetime plot based on start and end times of runs
* Correlation plot

By clicking *Show / Change ranges* button a *full screen mode* of a plot will be entered. In a *full screen mode* you can do one of the following things:

* Change the X and Y ranges of a plot
* Click on runs (data points) and reveal more information about them in the right hand side panel
* See the DQM histogram(s) that was used to extract the value of a trend in the right hand side panel
* Look at a selected run in DQM GUI, OMS and Run Registry
* Add or remove series from the plot dynamically by clicking *Add series to this plot*

# API documentation

This very API is powering the web application. No other, hidden API services are used. The web page is all static - no server rendering. 

**All endpoints should be used by making an HTTP GET request and providing the arguments in the url.**

## Endpoints

* `/api/data` 
* `/api/selection`
* `/api/plot_selection`
* `/api/runs`
* `/api/expand_url`

Let's talk about each of them one by one.

### `/api/data` 

This is the main endpoint used to retrieve historic DQM data.

Possible arguments:

| Param             | Data type  | Required/Optional                                                                          | Description                                                                                             |
|-------------------|------------|--------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| subsystem         | string     | required                                                                                   | Name of the subsystem. Possible values come from `/api/selection` endpoint.                            |
| pd                | string     | required                                                                                   | Name of the primary dataset. Possible values come from `/api/selection` endpoint.                      |
| processing_string | string     | required                                                                                   | Name of the processing string. Possible values come from `/api/selection` endpoint.                    |
| from_run          | int        | required together with `to_run`. Both can be substituted with either `runs` or `latest`.   | Runs filter: lower bound.                                                                               |
| to_run            | int        | required together with `from_run`. Both can be substituted with either `runs` or `latest`. | Runs filter: upper bound.                                                                               |
| runs              | array<int> | required but can be substituted with `from_run`, `to_run` or `latest`.                     | Runs filter: *comma separated* list of runs to return data for.                                           |
| latest            | int        | required but can be substituted with `from_run`, `to_run` or `runs`.                       | Runs filter: return latest N runs.                                                                      |
| series            | string     | optional                                                                                   | Specific name of the series to return. If not specified, all series will be returned based on selection. |
| series_id         | int        | optional                                                                                   | Specific series ID. IDs come from `/api/plot_selection` endpoint.                                       |

Keep in mind that runs can be filtered in 3 ways: 
* Range (`from_run`, `to_run`)
* List of specific runs (`runs`)
* Last N runs (`latest`)

**Exactly one way must be used to filter out required runs**.

Sample query: `/api/data?subsystem=PixelPhase1&pd=SingleElectron&processing_string=09Aug2019_UL2017&latest=50`

### `/api/selection` 

This endpoint returns a nested object of possible `subsystem`, `primary dataset` and `processing string` combinations. This endpoint takes no arguments.

Sample (shortened) response:

``` json
{
  "CSC":{
    "Cosmics":[
      "PromptReco"
    ],
    "JetHT":[
      "09Aug2019_UL2017"
    ]
  },
  "Muons":{
    "ZeroBias":[
      "09Aug2019_UL2017",
      "PromptReco"
    ]
  }
}
```

### `/api/plot_selection`

This endpoint is very similar to `/api/selection`, but it is one level deeper. It also includes the names and IDs of all available series. Names and IDs can be used to retrieve only **required** plots using `series` or `series_id` parameters in `/api/data` endpoint. This endpoint takes no arguments.

Sample (shortened) response:

``` json
{
  "CSC":{
    "Cosmics":{
      "PromptReco":[
        {
          "id":4426,
          "name":"AnodeCatodheTimeDiff"
        }
      ]
    }
  }
}
```

### `/api/runs`

This endpoint returns a list of all run numbers present in the HDQM database. This endpoint takes no arguments.

### `/api/expand_url`

For performance reasons, DQM GUI URLs for each data point are not returned by the `/api/data` endpoint. However, the data point IDs are returned and using this endpoint they can be exchanged for an actual DQM GUI URL.

Possible arguments:

| Param         | Data type | Required/optional | Description                                                                                                                                                                                                                      |
|---------------|-----------|-------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| data_point_id | int       | required          | An ID referring to a single data point returned by the `/api/data` endpoint.                                                                                                                                                     |
| url_type      | string    | required          | Type of the DQM GUI URL required. All possible values are: `main_gui_url`, `main_image_url`, `optional1_gui_url`, `optional1_image_url`, `optional2_gui_url`, `optional2_image_url`, `reference_gui_url`, `reference_image_url`. |

# Administration instructions

Production service is running on a public port 80 and test service on 81.
Production API server is running on internal port 5000 and test API service on 5001.

**Before doing anything become the correct user:**  
`sudo su cmsdqm`

Code is located in `/data/hdqm/` directory.

EOS and CVMFS file systems need to be accessible in order for the service to work. ROOT input files are coming EOS, and CMSSW release is comming from CVMFS.

Nginx configuration for a reverse proxy can be found here: `/etc/nginx/conf.d/`

Systemctl service for an API server can be found here: `/etc/systemd/system/hdqm.service`

Starting reverse proxy (nginx):
`sudo systemctl start nginx.service`

Starting an API service:  
`sudo systemctl start hdqm.service`

Packages are installed locally in `backend/.python_packages/python2` and `backend/.python_packages/python3` directories, for different python versions. Extractor and calculator are using python 2 as they rely on ROOT but an API Flask service is running on python 3. Make sure an appropriate python path is set before using the tools by hand. For example (running from `backend` directory):

```bash 
export PYTHONPATH="${PYTHONPATH}:$(pwd)/.python_packages/python2"
```

If nginx complains that it can't bind to port, make sure to request the ports to be opened in puppet:  
https://gitlab.cern.ch/ai/it-puppet-hostgroup-vocms/merge_requests/72  

And open them using SELinux: `sudo semanage port -m -t http_port_t -p tcp 8081`  
Also important:  
`sudo firewall-cmd --zone=public --add-port=81/tcp --permanent`  
`sudo firewall-cmd --reload`  
Make sure to make root directory accessible in SELinux:  
`chcon -Rt httpd_sys_content_t /data/hdqmTest/CentralHDQM/frontend/`  
`sudo chcon -Rt httpd_sys_content_t /data/hdqm/`

DB authentication information is placed in this file: `backend/connection_string.txt`, in the first line of said file, in this format: `postgres://<DB_NAME>:<PASSWORD>@<HOST>:<PORT>/<USER>`


## API local setup instructions

Before running the API server there should be a `backend/api/private/` folder containing these files:
* `userkey.pem` - GRID certificate key file
* `usercert.pem` - GRID certificate file

### Instructions on how to retrieve the certificate and the key:

* Get GRID certificate: https://ca.cern.ch/ca/ You have to use your personal account. **Certificate has to be passwordless**.
* Instructions on how to get certificate and key files: https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookStartingGrid#ObtainingCert
* Copy paste-ble instructions:
```
# Leave Import Password blank
# PEM passphrase is required to be set
openssl pkcs12 -in myCertificate.p12 -clcerts -nokeys -out usercert.pem
openssl pkcs12 -in myCertificate.p12 -nocerts -out userkey.tmp.pem
openssl rsa -in userkey.tmp.pem -out userkey.pem
```

### How to get cern_cacert.pem 

This CERN CA bundle is retreived from here: http://linuxsoft.cern.ch/cern/centos/7/cern/x86_64/repoview/CERN-CA-certs.html

Now, this file is used only for OMS requests.

## Daily extraction

HDQM automatically extracts data from EOS on a daily basis. This is done using systemctl timer.  
A timer `hdqm-extract.timer` launches `hdqm-extract.service` service every day. In order to stop the timer run:  
```bash
sudo systemctl stop hdqm-extract.timer
```
To get info about a timer run one of these two commands:
```bash
sudo systemctl list-timers
sudo systemctl status hdqm-extract.timer
```

Show the log of the service:

``` bash
sudo journalctl -u hdqm-extract
```

Service configuration files are located here: `/etc/systemd/system/`

### EOS access

**Extraction is performed on behalf of *cmsdqm* user because we need a user that would be in CERN.CH domain to access EOS file system**

User credentials are stored in a keytab file. This file needs to be updated when the password changes. Bellow are the instructions on how to do that:

``` bash
sudo su cmsdqm
ktutil
# Keep in mind the capital letters - they are important!
add_entry -password -p cmsdqm@CERN.CH -k 1 -e aes256-cts-hmac-sha1-96
add_entry -password -p cmsdqm@CERN.CH -k 1 -e arcfour-hmac
write_kt /data/hdqm/.keytab
exit
# Get the kerberos token. This will grant access to EOS
kinit -kt /data/hdqm/.keytab cmsdqm
# Make EOS aware of the new kerberos token
/usr/bin/eosfusebind -g
```

``` bash
# Verify
klist -kte /data/hdqm/.keytab
```

More info about kerberos: https://twiki.cern.ch/twiki/bin/view/Main/Kerberos

## How to update

The following script will pull a latest version of the HDQM code from a `https://github.com/cms-DQM/CentralHDQM` repository. It will copy required secret files from `private` directory, and point `current` symlink to the newly created version. 

```bash
ssh vocms0231
cd /data/hdqm
sudo su cmsdqm
./update.sh
exit
sudo systemctl restart hdqm.service
```

### How to rollback to the old version

In order to rollback to the previous version set `current` symlink to point to the required version folder (in the same directory) and restart the service:

```bash
cd /data/hdqm
ln -s -f -n <FOLDER_OF_THE_REQUIRED_VERSION> current
sudo systemctl restart hdqm.service
```
