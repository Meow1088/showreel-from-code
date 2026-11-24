# Full pipeline (Windows): music -> preview frames -> render -> QA gate.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
python music.py;                                   if ($LASTEXITCODE) { exit $LASTEXITCODE }
python render.py preview 2 5 10.8;                 if ($LASTEXITCODE) { exit $LASTEXITCODE }
python render.py video out/showreel.mp4 out/music.wav; if ($LASTEXITCODE) { exit $LASTEXITCODE }
python check.py out/showreel.mp4;                  exit $LASTEXITCODE
