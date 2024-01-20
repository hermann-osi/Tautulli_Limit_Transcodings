
"""
Description: Checks if the limit of current transcoding has been reached and calls
killscript : https://github.com/blacktwin/JBOPS/blob/master/killstream/kill_stream.py
to terminate the triggering stream.
Author : BalleRegente 

Adding the script to Tautulli:
Tautulli > Settings > Notification Agents > Add a new notification agent >
 Script

Configuration:
Tautulli > Settings > Notification Agents > New Script > Configuration:

 Script Folder: /path/to/your/scripts
 Script File: ./limit_transcodes.py 
 Script Timeout: {timeout}
 Description: Limit transcodings
 Save

Script Arguments:
Tautulli > Settings > Notification Agents > New Script > Script Arguments:
 -r, --resolution : to set the resolution to be monitored
 -l, --limitation : to set the limitation of transcoding from set resolution
 Then you put the kill_script.py regular arguments

Example : 
 -r 720 -l3 --jbop[...] => Will trigger killscript if there are 3 720p transcodings
 -r 1080 -l3 -r 720 -l4 => Will trigger if there are 3 1080p or 4 720p transcodings
 The triggering stream is taken into account during the check so you may add it to
 your limitations :
  -r 4k -l2 if triggered by new 4K transcodes to limit 4K transcodes to 1 maximum

Full examples :
    -r 4k -l2 --jbop stream --username "admin" --sessionId {session_id} 
        --killMessage "There is already another 4K stream."
    With a Tautulli condition "Video Decision is transcode" and "Video resolution
    is 4k". This will allow only 1 4K transcode at all time

    -r 1080 -l2 --jbop stream --username "admin" --sessionId {session_id} 
        --killMessage "There is already 2 other 1080p transcoding."
    With a Tautulli condition "Video Decision is transcode" and "Video resolution
    is 4k". This will prevent 4K transcoding if there are already 2 or more 
    1080p transcodes.

"""


import requests
import os
import sys
import argparse
import subprocess
import json

killscript_name = "kill_script.py"
allowed_resolutions = ["4k", "1080", "720"]

def check_transcoding(res_pairs, args_remaining, tautulli_url, tautulli_apikey):
    """
    Checks the number of active transcodings for each specified resolution and
    calls an external script (kill_script.py) if the number of transcodings 
    exceeds the limitation.

    :param res_pairs: List of pairs (resolution, limitation).
    :param args_remaining: Remaining arguments to pass to the killscript.
    :param tautulli_url: URL of the Tautulli API.
    :param tautulli_apikey: API key for Tautulli.
    :return: 0 if all limitations are respected
    :return: 1 if limitation has been exceeded
    :return -1 if error
    """

    api_endpoint = f"{tautulli_url}?cmd=get_activity&apikey={tautulli_apikey}"

    try:
        response = requests.get(api_endpoint)
        response.raise_for_status()
        data = response.json()
        for resolution, limitation in res_pairs:
            limitation = int(limitation)
            transcode_count = sum(
                1 for session in data['response']['data']['sessions']
                if session['video_resolution'] == resolution and session['transcode_decision'] == 'transcode'
            )
            print(f"current streams : {resolution} = {transcode_count} / {limitation}")
            if transcode_count >= limitation:
                print(f"{limitation} streams are already transcoding {resolution} videos. Calling killscript")
                killscript = ['python', killscript_name] + args_remaining
                process = subprocess.run(killscript, text=True, capture_output=True)
                print(process.stdout)
                if process.stderr:
                    print(process.stderr)
                    return -1
                return 1
        return 0

    except requests.RequestException as e:
        print(f"Error making API request: {e}", file=sys.stderr)
        return -1
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}", file=sys.stderr)
        return -1
    except KeyError:
        print("Error parsing response data. Please check the Tautulli API response format.", file=sys.stderr)
        return -1

def validate_resolutions(res_pairs):
    """
    Validates that each resolution in the pair is within the accepted values and that
    the limitation is an integer.

    :param res_pairs: List of pairs (resolution, limitation) to be validated.
    """

    for resolution, limitation in res_pairs:
        if resolution not in allowed_resolutions:
            raise ValueError(f"Invalid resolution set : {resolution}, accepted values are : {allowed_resolutions[:]}")
        
        try:
            limitation = int(limitation)
        except ValueError:
            raise ValueError(f"Limitation must be a number int : {limitation}")

def main():
    """
    Main function that parses arguments, validates resolutions, and checks transcoding
    limitations using Tautulli's API. This script triggers a killscript if limitations 
    are exceeded.
    """

    tautulli_apikey = os.getenv('TAUTULLI_APIKEY')
    tautulli_url = os.getenv('TAUTULLI_URL') + "/api/v2"

    parser = argparse.ArgumentParser(description='This script needs to be in the same location as killscript.py. \
            It will trigger killscript if it detects a certain amount of transcoding. For instance with --resolution 1080 -l2 \
            it will trigger if there already 2 streams (counting the current one) transcoding from 1080p.')
    parser.add_argument('-r', '--resolution', dest='resolution', action='append', default=[],
                        help='Specify the resolution to control [4k,1080,720]. Can be used multiple times like this : -r 4k -l1 -r 1080 \
                                -l2 -r 720 -l3 to limit 4k transcodes to 1, 1080p to 2, 720p to 3 ')
    parser.add_argument('-l', '--limitation', dest='limitation', action='append', default=[],
                        help='Specify the limitation to control the associated resolution')
    args, args_remaining = parser.parse_known_args()
    resolutions_tocheck = list(zip(args.resolution, args.limitation))
    if len(args.resolution) != len(args.limitation):
        print(f"There is a different number of resolution and limitation arguments. \
                Each resolution should have a corresponding limitation. \
                {len(args.resolution)} / {len(args.limitation)}", file=sys.stderr)
        for resolution, limitation in resolutions_tocheck:
            print(f"res = {resolution} / limit = {limitation}")
        return

    if not tautulli_apikey or not tautulli_url:
        print("Tautulli API key or URL is not set. Please check your configuration.", file=sys.stderr)
        return
    
    try:
        validate_resolutions(resolutions_tocheck)
    except ValueError as e:
        print(f"Error in resolution validation: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)
    result = check_transcoding(resolutions_tocheck, args_remaining, tautulli_url, tautulli_apikey)
    if result == 0:
        print("Limitations are all within limits.")
        sys.exit(0)
    elif result == 1:
        print("A limitation has been reached so killscript has been launched.")
        sys.exit(0)
    elif result == -1:
        print("The script has finished with errors. The check may not have been done properly.", file=sys.stderr)
        sys.exit(1)
      
if __name__ == "__main__":
    main()