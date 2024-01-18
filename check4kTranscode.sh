#!/bin/bash

# Path to the kill_script.py
killscript_path="/config/killscript.py"

get_actual_4k_transcode_count() {
    local tautulli_apikey="$TAUTULLI_APIKEY" #"$TAUTULLI_APIKEY" #"YOUR_TAUTULLI_API_KEY"
    local tautulli_url="$TAUTULLI_URL/api/v2" #"http://your-tautulli-host:8181/api/v2"


    local api_endpoint="${tautulli_url}?cmd=get_activity&apikey=${tautulli_apikey}"
    local response=$(curl -s "${api_endpoint}")
    echo "VOILA : $response" 1>&2
    # Count the number of 4K transcodes
    local transcode_count=$(echo "$response" | python -c "import sys, json
data = json.load(sys.stdin)
count = sum(1 for session in data['response']['data']['sessions'] if session['video_resolution'] == '4k' and session['transcode_decision'] == 'transcode')
print(count)
")
    echo "$transcode_count stream 4K currently playing / $tautulli_apikey / $tautulli_url" 1>&2
    echo $transcode_count
}

# Main logic
current_transcodes=$(get_actual_4k_transcode_count)

if [ "$current_transcodes" -ge 2 ]; then
    echo "A 4K transcode is already in progress. Calling killscript" 1>&2
    python $killscript_path "$@"
fi
