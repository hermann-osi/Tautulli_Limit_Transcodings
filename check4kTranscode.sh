#!/bin/bash

# Path to the kill_script.py
killscript_path="<PATH KILLSCRIPT>" #Change it to the path of killscript

get_actual_4k_transcode_count() {
    local tautulli_apikey="$TAUTULLI_APIKEY" 
    local tautulli_url="$TAUTULLI_URL/api/v2" 


    local api_endpoint="${tautulli_url}?cmd=get_activity&apikey=${tautulli_apikey}"
    local response=$(curl -s "${api_endpoint}")
    # Count the number of 4K transcodes
    local transcode_count=$(echo "$response" | python -c "import sys, json
data = json.load(sys.stdin)
count = sum(1 for session in data['response']['data']['sessions'] if session['video_resolution'] == '4k' and session['transcode_decision'] == 'transcode')
print(count)
")
    echo $transcode_count
}

# Main logic
current_transcodes=$(get_actual_4k_transcode_count)
echo "$current_transcodes stream 4K currently playing"
if [ "$current_transcodes" -ge 2 ]; then
    echo "A 4K transcode is already in progress. Calling killscript"
    python $killscript_path "$@"
fi
