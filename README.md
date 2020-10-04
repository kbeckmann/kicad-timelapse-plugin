# kicad-timelapse-plugin

To convert svg to png:

`parallel -k inkscape --export-type=png -w 1920 --export-area-drawing --export-background=black ::: *.svg`

To convert png to mp4

`ffmpeg -framerate 2 -pattern_type glob -i "*.png" -r 2 out.mp4`
