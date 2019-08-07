# uitabot
**uitabot** is a [Discord](https://discordapp.com/) music bot that can be controlled both via chat commands and a real time web client.

## Requirements
* [Discord API key](https://discordapp.com/developers)
* [YouTube API key](https://developers.google.com/youtube/v3/)
* Python 3.6
* npm
* ffmpeg & ffprobe (version 4 or newer needed for some live streams)

## Linux Installation from Source
### Setup
```
git clone https://github.com/tedle/uitabot.git
sudo apt-get install python3 python3-dev lib-ffi-dev npm
cd bot
pip install -r requirements.txt
cd ../web-client
npm install
```

### Configuration
Make a copy of the `config.example.json` in the root folder.
```
cp config.example.json config.json
```
Edit the new `config.json` file and fill in all the variables as needed. Documentation for every option can be found in [CONFIG.md](CONFIG.md).

### Building
#### Backend
```
cd bot
python uitabot.py
```
#### Frontend (development)
```
cd web-client
npm run dev
```
This will run a local web server that supports hot-reloading for development.
#### Frontend (production)
```
cd web-client
npm run build
```
This will output static asset files to the `web-client/build` folder that can then be served from any generic web server.

## Binary Installation
Not supported.

## License
[ISC License](https://github.com/tedle/uitabot/blob/master/LICENSE)
