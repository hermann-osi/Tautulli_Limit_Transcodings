#!/usr/bin/env python

"""
Description: Checks if the limit of current transcoding has been reached and calls
kill_stream : https://github.com/blacktwin/JBOPS/blob/master/killstream/kill_stream.py
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
 Then you put the kill_stream.py regular arguments
 -c, --limitation : (optional) Allow to combine with a defined ratio all
                    resolutions

Example : 
 -r 720 -l3 --jbop[...] => Will trigger kill_stream if there are 3 720p transcodings
 -r 1080 -l3 -r 720 -l4 => Will trigger if there are 3 1080p or 4 720p transcodings
 The triggering stream is taken into account during the check so you may add it to
 your limitations :
  -r 4k -l2 if triggered by new 4K transcodes to limit 4K transcodes to 1 maximum
  
 Combine ratio : 
  -r 4k -l2 -r 1080 -l3 -c2 => Will trigger if there are 2 4K transcodes, 2 1080p
  transcodes or a combination of 1080p/4K transcodes with 2 1080p being worth 1 4K.
  That means 2 1080p and 1 4K will trigger it. This make the script more likely to
  trigger since lower resolutions are counted for their own limits but also for the
  superior resolution's limit.

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

killstream_name = "kill_stream.py" # Edit here if you called kill_stream a different name or if you
                                   # want to trigger another script instead
allowed_resolutions = ["4k", "1080", "720", "480"]

resolution_hierarchy = {
    "480": 1,
    "720": 2,
    "1080": 3,
    "4k": 4
}

def check_transcoding(res_pairs, args_remaining, combine_ratio, verbose, tautulli_url, tautulli_apikey):
    """
    Checks the number of active transcodings for each specified resolution and
    calls an external script (kill_stream.py) if the number of transcodings 
    exceeds the limitation.

    :param res_pairs: List of pairs (resolution, limitation).
    :param args_remaining: Remaining arguments to pass to the kill_stream.
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
        resolution_count = {res: 0 for res in allowed_resolutions}
        for session in data['response']['data']['sessions']:
            if session['transcode_decision'] == 'transcode' and session['video_resolution'] in resolution_count:
                resolution_count[session['video_resolution']] += 1
        if combine_ratio > 0:
            if verbose:
                print("Combine ratio activated, lower resolutions may be counted twice (once for their own limitation, once for higher resolutions limitations)")
            user_resolutions = [res for res, _ in res_pairs]  # Get resolutions specified by the user
            # Filter allowed_resolutions to only include those specified by the user
            relevant_resolutions = [res for res in allowed_resolutions if res in user_resolutions]
            sorted_resolutions = sorted(relevant_resolutions, key=lambda x: resolution_hierarchy[x])
            for i in range(len(sorted_resolutions) - 1, 0, -1):
                current_res = sorted_resolutions[i]
                next_lower_res = sorted_resolutions[i - 1]
                # Combine lower resolution count into the current resolution
                if current_res in user_resolutions and next_lower_res in user_resolutions:
                    combined_count = resolution_count[next_lower_res] // combine_ratio
                    resolution_count[current_res] += combined_count
                    tot_combined_count = combined_count * combine_ratio
                    if verbose:
                        print(f'Combined {tot_combined_count} counts of {next_lower_res} into {combined_count} counts of {current_res}. Remaining {next_lower_res}: {resolution_count[next_lower_res]}')
        for resolution, limitation in res_pairs:
            limitation = int(limitation)
            transcode_count = resolution_count[resolution]
            if verbose:
                print(f"current streams : {resolution} = {transcode_count} / {limitation}")
            if transcode_count >= limitation:
                print(f"{limitation} streams are already transcoding {resolution} videos. Calling kill_stream")
                kill_stream = ['python', killstream_name] + args_remaining
                process = subprocess.run(kill_stream, text=True, capture_output=True)
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
    limitations using Tautulli's API. This script triggers a kill_stream if limitations 
    are exceeded.
    """

    tautulli_apikey = os.getenv('TAUTULLI_APIKEY')
    tautulli_url = os.getenv('TAUTULLI_URL') + "/api/v2"

    parser = argparse.ArgumentParser(description='This script needs to be in the same location as kill_stream.py. \
            It will trigger kill_stream if it detects a certain amount of transcoding. For instance with --resolution 1080 -l2 \
            it will trigger if there already 2 streams (counting the current one) transcoding from 1080p.')
    parser.add_argument('-r', '--resolution', dest='resolution', action='append', default=[],
                        help='Specify the resolution to control [4k,1080,720]. Can be used multiple times like this : -r 4k -l1 -r 1080 \
                                -l2 -r 720 -l3 to limit 4k transcodes to 1, 1080p to 2, 720p to 3 ')
    parser.add_argument('-l', '--limitation', dest='limitation', action='append', default=[],
                        help='Specify the limitation to control the associated resolution')
    parser.add_argument('-c', '--combine', dest='combine', type=int, default=0,
                        help='Specify a ratio at which resolution counts need to be combined : 2 means that 2 720p transcodes are worth \
                                1 superior (here 1080p) transcode')
    parser.add_argument('-v', '--verbose', action='store_true', help='Increase output verbosity')
    args, args_remaining = parser.parse_known_args()
    if args.combine < 1 and args.combine != 0:
        print("Invalid combine ratio. The ratio must be a positive integer.", file=sys.stderr)
        sys.exit(1)
    resolutions_tocheck = list(zip(args.resolution, args.limitation))
    if len(args.resolution) != len(args.limitation):
        print(f"There is a different number of resolution and limitation arguments. \
                Each resolution should have a corresponding limitation. \
                {len(args.resolution)} / {len(args.limitation)}", file=sys.stderr)
        if args.verbose:
            for resolution, limitation in resolutions_tocheck:
                print(f"res = {resolution} / limit = {limitation}")
        sys.exit(1)

    if not tautulli_apikey or not tautulli_url:
        print("Tautulli API key or URL is not set. Please check your configuration.", file=sys.stderr)
        sys.exit(1)
    
    try:
        validate_resolutions(resolutions_tocheck)
    except ValueError as e:
        print(f"Error in resolution validation: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)
    result = check_transcoding(resolutions_tocheck, args_remaining, args.combine, args.verbose, tautulli_url, tautulli_apikey)
    if result == 0:
        print("Transcodings are all within limits.")
        sys.exit(0)
    elif result == 1:
        print("A limitation has been reached so kill_stream has been launched.")
        sys.exit(0)
    elif result == -1:
        print("The script has finished with errors. The check may not have been done properly.", file=sys.stderr)
        sys.exit(1)
if __name__ == "__main__":
    main()
