### RUN CODE
cd PROJECT_ROOT/
python -m venv venv
./venv/Scripts/Activate.ps1
python -m pip install --upgrade pip
pip install -r ./requirements.txt
python main.py

### CREATE EXEC
pip install pyinstaller (with venv)

> https://imagemagick.org/script/download.php

magick res/app_icon.png -define icon:auto-resize=16,24,32,48,64,128,256 -compress zip ./res/app_icon.ico

pyinstaller --clean --onefile --windowed --icon=./res/app_icon.ico main.py --add-data "res;res"
