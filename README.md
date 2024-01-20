# Tautulli-check-only-one-transcoding-4K
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
