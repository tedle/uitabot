## 1.1.0 (Jun 6, 2020)

### New features
- Add `.nowplaying` command to show currently playing song in chat

### Fixes
- Better voice connection logic for fewer stalls in poor network conditions
- Update frontend dependencies for various security fixes

## 1.0.3 (Feb 7, 2020)

- Fix playback regression of audio streams

## 1.0.2 (Nov 19, 2019)

- Fix client error when Youtube videos have no thumbnails

## 1.0.1 (Oct 19, 2019)

- Update backend dependencies
  - Fixes voice channel connection timeouts
  - Fixes Youtube audio playback
- Fix IP binding in isolated networks

## 1.0.0 (Sep 13, 2019)

### New features & changes
- Add `.set-role <ROLE>` command to restrict bot usage in a server
- Channel categories are now shown and sorted properly
- Channels that can't be joined are no longer shown in the UI
- Extend file upload timeout window for slow connections
- Playback progress meter shows as empty for live streams
- Video files can now be uploaded and streamed (audio only)

### Internal changes
- Bug fixes
- Add continuous integration for testing and build verification
- Add database file config setting, allowing for persistent storage of server options and temporary credentials
- Add trial mode config setting, allowing for a publically hosted demo bot
- Add verbose logging config setting for easier debugging
- Add project wide testing for faster, more reliable maintenance and development
- Update backend dependencies for security

## 0.2.0 (Jul 3, 2019)

- Update backend dependencies
  - New version of discord.py allows for automatic reconnections
  - New version of FFmpeg fixes playing certain YouTube live streams
  - New version of youtube-dl fixes YouTube video playback
- Update frontend dependencies for various security fixes
- Fix errors with cancelled file uploads
- Fix common ports not properly truncating in URLs

## 0.1.0 (May 18, 2018)

- Initial release
