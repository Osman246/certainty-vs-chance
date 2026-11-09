# The LinkedIn video

`render.py` draws every frame from the project's data files (1080×1350, 30 fps) and encodes it with ffmpeg.

```bash
mkdir -p video/fonts   # EB Garamond and Inter, both SIL Open Font License, from Google Fonts:
curl -L -o "video/fonts/EBGaramond[wght].ttf"        "https://raw.githubusercontent.com/google/fonts/main/ofl/ebgaramond/EBGaramond%5Bwght%5D.ttf"
curl -L -o "video/fonts/EBGaramond-Italic[wght].ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/ebgaramond/EBGaramond-Italic%5Bwght%5D.ttf"
curl -L -o "video/fonts/Inter.ttf"                   "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz,wght%5D.ttf"
python run_pipeline.py && python video/render.py      # one .mp4 per scene in video/out
```
Colour means one thing throughout: ochre = chance (prizes), teal = certainty (guaranteed rewards).
