{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "import requests\n",
    "import pandas as pd\n",
    "import json\n",
    "from time import time, sleep\n",
    "from os import mkdir, listdir, path, getcwd, chdir\n",
    "import gpxpy.gpx\n",
    "from datetime import datetime, timedelta\n",
    "from argparse import ArgumentParser\n",
    "\n",
    "\n",
    "class StravaApiHelper:\n",
    "\tdef __init__(self, args=None):\n",
    "\t\tprint(f'Current directory: {getcwd()}')\n",
    "\t\tif args == None:\n",
    "\t\t\tself.keys_folder = 'keys/'\n",
    "\t\t\tself.data_folder = 'data/'\n",
    "\t\telse:\n",
    "\t\t\tif args.keys[-1] == '\\\\' or args.data[-1] == '\\\\':\n",
    "\t\t\t\traise ValueError(\n",
    "\t\t\t\t\t'Please use unix style folder separation. i.e. path/to/file')\n",
    "\t\t\tif args.dir != 'n/a':\n",
    "\t\t\t\tchdir(args.dir)\n",
    "\t\t\tself.keys_folder = args.keys if args.keys[-1] == '/' else args.keys + '/'\n",
    "\t\t\tself.data_folder = args.data if args.data[-1] == '/' else args.data + '/'\n",
    "\t\tself.exceed_counter = 0\n",
    "\t\tprint(f'Data printed to: {self.data_folder}')\n",
    "\t\tprint(f'API tokens stored in: {self.keys_folder}')\n",
    "\t\tfor f in [self.keys_folder, self.data_folder, self.data_folder + 'figs']:\n",
    "\t\t\tif not path.isdir(f):\n",
    "\t\t\t\tmkdir(f)\n",
    "\t\t\t\tprint(f'Made folder: {f}')\n",
    "\n",
    "\tdef GetInitialStravaTokens(self):\n",
    "\t\twith open(self.keys_folder + 'client_info.json') as f:\n",
    "\t\t\tinit_info = json.load(f)\n",
    "\t\tresponse = requests.post(\n",
    "\t\t\turl='https://www.strava.com/oauth/token',\n",
    "\t\t\tdata=init_info\n",
    "\t\t)  # Save json response as a variable\n",
    "\t\tstrava_tokens = response.json()\n",
    "\t\twith open(self.keys_folder + 'strava_tokens.json', 'w') as outfile:\n",
    "\t\t\tjson.dump(strava_tokens, outfile)\n",
    "\t\twith open(self.keys_folder + 'strava_tokens.json') as check:\n",
    "\t\t\tdata = json.load(check)\n",
    "\t\tprint('The following was written to strava_tokens.json:\\n', data)\n",
    "\t\tif 'errors' in [*data]:\n",
    "\t\t\traise ValueError(\n",
    "\t\t\t\t'Unable to retrieve API tokens place an updated code in client_info.json')\n",
    "\n",
    "\tdef GetUpdatedStravaTokens(self):\n",
    "\t\tif 'strava_tokens.json' not in listdir(self.keys_folder):\n",
    "\t\t\tself.GetInitialStravaTokens()\n",
    "\t\twith open(self.keys_folder + 'strava_tokens.json') as json_file:\n",
    "\t\t\t# If access_token has expired then\n",
    "\t\t\tstrava_tokens = json.load(json_file)\n",
    "\n",
    "\t\t# use the refresh_token to get the new access_token\n",
    "\t\t# Make Strava auth API call with current refresh token\n",
    "\t\tif strava_tokens['expires_at'] < time():\n",
    "\n",
    "\t\t\twith open(self.keys_folder + 'client_info.json') as f:\n",
    "\t\t\t\tinit_info = json.load(f)\n",
    "\t\t\tclient_id = init_info['client_id']\n",
    "\t\t\tclient_secret = init_info['client_secret']\n",
    "\n",
    "\t\t\tresponse = requests.post(\n",
    "\t\t\t\turl='https://www.strava.com/oauth/token',\n",
    "\t\t\t\tdata={\n",
    "\t\t\t\t\t'client_id': client_id,\n",
    "\t\t\t\t\t'client_secret': client_secret,\n",
    "\t\t\t\t\t'grant_type': 'refresh_token',\n",
    "\t\t\t\t\t'refresh_token': strava_tokens['refresh_token']\n",
    "\t\t\t\t}\n",
    "\t\t\t)  # Save response as json in new variable\n",
    "\t\t\tnew_strava_tokens = response.json()  # Save new tokens to file\n",
    "\t\t\twith open(self.keys_folder + 'strava_tokens.json', 'w') as outfile:\n",
    "\t\t\t\t# Use new Strava tokens from now\n",
    "\t\t\t\tjson.dump(new_strava_tokens, outfile)\n",
    "\t\t\t# Open the new JSON file and print the file contents\n",
    "\t\t\tstrava_tokens = new_strava_tokens\n",
    "\n",
    "\tdef GetInitialData(self):\n",
    "\t\t\"\"\"\n",
    "\t\tThis function is unused but is handy if you want to see all\n",
    "\t\tavailable fields that could be included in activity summary.\n",
    "\t\t\"\"\"\n",
    "\t\twith open(self.keys_folder + 'strava_tokens.json') as json_file:\n",
    "\t\t\tstrava_tokens = json.load(json_file)  # Loop through all activities\n",
    "\t\turl = \"https://www.strava.com/api/v3/activities\"\n",
    "\t\t# Get first page of activities from Strava with all fields\n",
    "\t\taccess_token = strava_tokens['access_token']\n",
    "\t\tr = requests.get(url + '?access_token=' + access_token)\n",
    "\t\tr = r.json()\n",
    "\t\tdf = pd.json_normalize(r)\n",
    "\t\tdf.to_csv('strava_activities_all_fields.csv')\n",
    "\n",
    "\tdef GetActivitySummary(self, recent=True):\n",
    "\t\tprint('Getting activity summary...')\n",
    "\t\tcols = ('id', 'name', 'manual', 'distance', 'moving_time',\n",
    "                'total_elevation_gain',\t'type', 'start_date_local',\n",
    "                'average_speed', 'average_cadence', 'weighted_average_watts',\n",
    "                'average_heartrate', 'max_heartrate', 'start_latlng')\n",
    "\n",
    "\t\t# Get the tokens from file to connect to Strava\n",
    "\t\twith open(self.keys_folder + 'strava_tokens.json') as json_file:\n",
    "\t\t\tstrava_tokens = json.load(json_file)  # Loop through all activities\n",
    "\t\tpage = 1\n",
    "\t\turl = \"https://www.strava.com/api/v3/activities\"\n",
    "\t\t# Create the dataframe ready for the API call to store your activity data\n",
    "\t\taccess_token = strava_tokens['access_token']\n",
    "\t\tif 'activity_summary_raw.csv' in listdir(self.data_folder):\n",
    "\t\t\tactivities = pd.read_csv(\n",
    "\t\t\t\tself.data_folder + 'activity_summary_raw.csv')\n",
    "\t\telse:\n",
    "\t\t\tactivities = pd.DataFrame(columns=cols)\n",
    "\t\tnew_activities = pd.DataFrame(columns=cols)\n",
    "\t\tflag = True\n",
    "\t\twhile flag:\n",
    "\t\t\t# get page of activities from Strava\n",
    "\t\t\tr = requests.get(url + '?access_token=' + access_token +\n",
    "\t\t\t\t\t\t\t '&per_page=200' + '&page=' + str(page))\n",
    "\t\t\tr = r.json()\n",
    "\n",
    "\t\t\tif isinstance(r, dict):\n",
    "\t\t\t\tcheck = r['message']\n",
    "\t\t\t\tif check == 'Rate Limit Exceeded':\n",
    "\t\t\t\t\tprint('Rate Limit Exceeded, sleeping for 15 mins')\n",
    "\t\t\t\t\tself.exceed_counter += 1\n",
    "\t\t\t\t\tif self.exceed_counter >= 10:\n",
    "\t\t\t\t\t\texit('Over number of daily API requests\\nRestart tomorrow')\n",
    "\t\t\t\t\tsleep(20)\n",
    "\t\t\t\t\tfor i in range(15):\n",
    "\t\t\t\t\t\tprint(f'Sleep remaining:{int(15-i)} minutes')\n",
    "\t\t\t\t\t\tsleep(60)\n",
    "\t\t\t\t\tr = requests.get(\n",
    "\t\t\t\t\t\turl + '?access_token=' + access_token + '&per_page=200' + '&page=' + str(page))\n",
    "\t\t\t\t\tr = r.json()\n",
    "\n",
    "\t\t\t# if no results then exit loop\n",
    "\t\t\tif not r:  # if nothing to return\n",
    "\t\t\t\tbreak\n",
    "\t\t\t# otherwise add new data to dataframe\n",
    "\t\t\tfor x in range(len(r)):\n",
    "\t\t\t\tif int(r[x]['id']) in activities['id'].to_list():\n",
    "\t\t\t\t\tflag = False\n",
    "\t\t\t\t\tbreak\n",
    "\t\t\t\tfor col in cols:\n",
    "\t\t\t\t\tvalue = r[x][col] if col in r[x].keys() else 0\n",
    "\t\t\t\t\tnew_activities.loc[x + (page - 1) * 200, col] = value\n",
    "\t\t\tpage += 1  # Export your activities file as a csv\n",
    "\t\t# to the folder you're running this script in\n",
    "\t\tnew_activities = new_activities.append(activities, ignore_index=True)\n",
    "\t\tnew_activities.to_csv(\n",
    "\t\t\tself.data_folder + 'activity_summary_raw.csv', index=False)\n",
    "\t\tprint('Activity summary updated!')\n",
    "\n",
    "\tdef GetGPXFile(self, supress=True):\n",
    "\t\tprint('Downloading GPX files...')\n",
    "\t\tif 'gpx' not in listdir(self.data_folder):\n",
    "\t\t\tmkdir(self.data_folder + '/gpx')\n",
    "\t\twith open(self.keys_folder + 'strava_tokens.json') as json_file:\n",
    "\t\t\tstrava_tokens = json.load(json_file)\n",
    "\t\taccess_token = strava_tokens['access_token']\n",
    "\t\theader = {'Authorization': 'Bearer ' + access_token}\n",
    "\t\tparam = {'keys': ['latlng']}\n",
    "\n",
    "\t\tid_list = pd.read_csv(self.data_folder + 'activity_summary_raw.csv',\n",
    "\t\t\t\t\t\t\t  usecols=['id', 'start_date_local', 'type', 'manual', 'start_latlng'])\n",
    "\t\tfor idx in id_list.index:\n",
    "\t\t\tid = id_list.loc[idx, 'id']\n",
    "\t\t\tif id_list.loc[idx, 'manual']:\n",
    "\t\t\t\tif not supress:\n",
    "\t\t\t\t\tprint(f'Skipping manual activity: {id}')\n",
    "\t\t\t\tcontinue\n",
    "\t\t\t# act_type = id_list.loc[idx,'type']\n",
    "\t\t\t# if act_type not in ['Run', 'Walk', 'Hike', 'Ride']:\n",
    "\t\t\t#     if not supress:\n",
    "\t\t\t#         print(f'Skipping activity type: {act_type}')\n",
    "\t\t\t#     continue\n",
    "\t\t\tif len(id_list.loc[idx, 'start_latlng'].split(',')) != 2:\n",
    "\t\t\t\tif not supress:\n",
    "\t\t\t\t\tprint(f'Skipping activity, no GPS: {id}')\n",
    "\t\t\t\tcontinue\n",
    "\n",
    "\t\t\tstart_time = id_list.loc[idx, 'start_date_local']\n",
    "\n",
    "\t\t\tif f'{id}.gpx' in listdir(f'{self.data_folder}/gpx/'):\n",
    "\t\t\t\tcontinue  # skip activities that are alre\n",
    "\n",
    "\t\t\turl = f\"https://www.strava.com/api/v3/activities/{id}/streams\"\n",
    "\t\t\tlatlong = requests.get(url, headers=header, params={\n",
    "\t\t\t\t\t\t\t\t   'keys': ['latlng']}).json()\n",
    "\t\t\ttime_list = requests.get(url, headers=header, params={\n",
    "\t\t\t\t\t\t\t\t\t 'keys': ['time']}).json()\n",
    "\t\t\taltitude = requests.get(url, headers=header, params={\n",
    "\t\t\t\t\t\t\t\t\t'keys': ['altitude']}).json()\n",
    "\n",
    "\t\t\tfor r in [latlong, time_list, altitude]:\n",
    "\t\t\t\tif isinstance(r, dict) and 'message' in r.keys():\n",
    "\t\t\t\t\tcheck = r['message']\n",
    "\t\t\t\t\tif check == 'Rate Limit Exceeded':\n",
    "\t\t\t\t\t\tprint('Rate Limit Exceeded, sleeping for 15 mins')\n",
    "\t\t\t\t\t\tself.exceed_counter += 1\n",
    "\t\t\t\t\t\tif self.exceed_counter >= 10:\n",
    "\t\t\t\t\t\t\texit('Over number of daily API requests\\nRestart tomorrow')\n",
    "\t\t\t\t\t\tsleep(20)\n",
    "\t\t\t\t\t\tfor i in range(15):\n",
    "\t\t\t\t\t\t\tprint(f'Sleep remaining: {int(15-i)} minutes')\n",
    "\t\t\t\t\t\t\tsleep(60)\n",
    "\t\t\t\t\t\tprint('Recommencing...')\n",
    "\t\t\t\t\t\tlatlong = requests.get(url, headers=header, params={\n",
    "\t\t\t\t\t\t\t\t\t\t\t   'keys': ['latlng']}).json()\n",
    "\t\t\t\t\t\ttime_list = requests.get(url, headers=header, params={\n",
    "\t\t\t\t\t\t\t\t\t\t\t\t 'keys': ['time']}).json()\n",
    "\t\t\t\t\t\taltitude = requests.get(url, headers=header, params={\n",
    "\t\t\t\t\t\t\t\t\t\t\t\t'keys': ['altitude']}).json()\n",
    "\t\t\t\t\t\tbreak\n",
    "\n",
    "\t\t\tlatlong = latlong[0]['data']\n",
    "\t\t\ttime_list = time_list[1]['data']\n",
    "\t\t\taltitude = altitude[1]['data']\n",
    "\n",
    "\t\t\tdata = pd.DataFrame([*latlong], columns=['lat', 'long'])\n",
    "\t\t\tdata['altitude'] = altitude\n",
    "\t\t\tstart_time = datetime.strptime(start_time, \"%Y-%m-%dT%H:%M:%SZ\")\n",
    "\t\t\tdata['time'] = [(start_time + timedelta(seconds=t))\n",
    "\t\t\t\t\t\t\tfor t in time_list]\n",
    "\n",
    "\t\t\tgpx = gpxpy.gpx.GPX()\n",
    "\t\t\t# Create first track in our GPX:\n",
    "\t\t\tgpx_track = gpxpy.gpx.GPXTrack()\n",
    "\t\t\tgpx.tracks.append(gpx_track)\n",
    "\t\t\t# Create first segment in our GPX track:\n",
    "\t\t\tgpx_segment = gpxpy.gpx.GPXTrackSegment()\n",
    "\t\t\tgpx_track.segments.append(gpx_segment)\n",
    "\n",
    "\t\t\t# Create points:\n",
    "\t\t\tfor idx in data.index:\n",
    "\t\t\t\tgpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(\n",
    "\t\t\t\t\tdata.loc[idx, 'lat'], data.loc[idx, 'long'], elevation=data.loc[idx, 'altitude'], time=data.loc[idx, 'time']))\n",
    "\n",
    "\t\t\twith open(f'{self.data_folder}/gpx/{id}.gpx', 'w') as f:\n",
    "\t\t\t\tf.write(gpx.to_xml())\n",
    "\t\tprint('Finished downloading GPX files!')\n",
    "\n",
    "\n",
    "def main(args):\n",
    "\thelper = StravaApiHelper(args)\n",
    "\thelper.GetUpdatedStravaTokens()\n",
    "\thelper.GetActivitySummary()\n",
    "\thelper.GetGPXFile()\n",
    "\n",
    "if __name__ == '__main__':\n",
    "\tparser = ArgumentParser(description='Create GPX files from streams downloaded using StravaAPI',\n",
    "\t\t\t\t\t\t\tepilog='Report issues to... ')\n",
    "\tparser.add_argument('--dir', default='n/a',\n",
    "\t\t\t\t\t\thelp='Current working directory. Data and Keys are specified relative to this.')\n",
    "\tparser.add_argument('--data', default='data',\n",
    "\t\t\t\t\t\thelp='Data files directory - will contain activity summary and folder of gpx files')\n",
    "\tparser.add_argument('--keys', default='keys',\n",
    "\t\t\t\t\t\thelp='Folder containing client_info.json and strava_tokens.json')\n",
    "\targs = parser.parse_args()\n",
    "\tmain(args)"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "venv",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "name": "python",
   "version": "3.11.4 (main, Jun  6 2023, 22:16:46) [GCC 11.3.0]"
  },
  "orig_nbformat": 4,
  "vscode": {
   "interpreter": {
    "hash": "68e95443b65cde8e8f0b8ccc1756d4df7bb5e9142ecd5733ba8dfbe5c245fcf2"
   }
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}
