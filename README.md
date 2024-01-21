# Limit transcodings
This is a little script meant to be an add-on to kill_script.py : https://github.com/blacktwin/JBOPS/blob/master/killstream/kill_stream.py
You put limite_transcodes.py in the same folder as kill_script.py and then you can directly set it in Tautulli.

# Examples :
If we want to limit 4K streamings to maximum 1 transcode at all times :

To set the script :


<img src="https://res.cloudinary.com/dmkxca49o/image/upload/c_pad,b_auto:predominant,fl_preserve_transparency/v1705765270/Capture_d_écran_2024-01-20_à_16.39.24_tlljvg.jpg" width="400" height="400">

To set the conditions :

<img src="https://res.cloudinary.com/dmkxca49o/image/upload/v1705766284/Capture_d_%C3%A9cran_2024-01-20_%C3%A0_16.57.40_bzrtrw.png" width="400" height="400">

To set the arguments (-r resolution -l nbr of streams before triggering killscript [+ normal kill_script args])  :

<img src="https://res.cloudinary.com/dmkxca49o/image/upload/v1705766544/Capture_d_%C3%A9cran_2024-01-20_%C3%A0_17.02.07_fskkqb.png" width="400" height="400">

Notice the limitation is set to 2 and not 1 because the triggering stream is taken into account. If we set it to 1, no more 4k transcoding will be possible but we set it to 2 so the first one will be allowed and second one will trigger killscript.

You can also use the optional argument "-c, --combine" with a value to activate the combine feature. This will allow the script to combine all limitations according to the given ratio. "-c 2" will mean that every resolution is worth 2 times the resolution below (2 720p transcodings will be equal to 1 1080p transcoding). 
This can be used to have a coherent CPU load limit instead of covering every case individually. 

Be aware that when using the "-c, --combine" option, lower resolution streams are effectively counted twice: once for their own resolution and once as part of the combined count for the next higher resolution. For instance, using "-r 1080 -l2 -r 720 -l3 -c2" with 3 720p transcoding streams will result in these streams being counted as 3 720p transcodes and additionally as 1 1080p transcode due to the combining ratio. This behavior makes the script more restrictive, as it will trigger the kill script based on the limitations of both the individual resolution and the combined higher resolution.

-v, --verbose is used to have more logs from Tautulli during the execution of the script.
