// --- YoutubeApi.js -----------------------------------------------------------
// YouTube API request functions

import * as Config from "config";
import TimestampFormat from "utils/TimestampFormat";

var ResultType = {
    VIDEO: 1,
    LIVE: 2,
    PLAYLIST: 3
};
Object.freeze(ResultType);

class Result {
    constructor(id, thumbnail, title, type, duration) {
        this.id = id;
        this.thumbnail = thumbnail;
        this.title = title;
        this.type = type;
        this.duration = duration;
    }

    get url() {
        switch(this.type) {
            case ResultType.VIDEO:
            case ResultType.LIVE:
                return `https://youtube.com/watch?v=${this.id}`;
            case ResultType.PLAYLIST:
                return `https://youtube.com/playlist?list=${this.id}`;
            default:
                return "";
        }
    }

    displayDuration() {
        switch(this.type) {
            case ResultType.VIDEO:
                if (this.duration == null) {
                    return "";
                }
                return TimestampFormat(this.duration);
            case ResultType.LIVE:
                return "Live";
            case ResultType.PLAYLIST:
                return "Playlist";
            default:
                return "";
        }
    }
}

export async function search(query) {
    // Make API request
    const url = `https://www.googleapis.com/youtube/v3/search/?`
        + `q=${encodeURI(query)}`
        + `&maxResults=10`
        + `&part=snippet`
        + `&type=video,playlist`
        + `&key=${Config.youtube_api}`;
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`YouTube API search query failed with status code ${response.status}`);
    }
    // Parse results
    const results = await response.json();
    return results.items.map(result => {
        let id = null;
        let type = null;
        switch (result.id.kind) {
            case "youtube#video":
                id = result.id.videoId;
                if (result.snippet.liveBroadcastContent == "live") {
                    type = ResultType.LIVE;
                }
                else {
                    type = ResultType.VIDEO;
                }
                break;
            case "youtube#playlist":
                id = result.id.playlistId;
                type = ResultType.PLAYLIST;
                break;
            default:
                throw new Error(`YouTube API returned unknown result type ${result.id.kind}`);
        }
        return new Result(
            id,
            result.snippet.thumbnails.medium.url,
            result.snippet.title,
            type,
            null
        );
    });
}

export async function searchDetails(results) {
    // Request additional details only for videos, not playlists
    const videoIds = results
        .filter(result => result.type == ResultType.VIDEO)
        .map(result => result.id);
    // Make API request
    const url = `https://www.googleapis.com/youtube/v3/videos/?`
        + `id=${videoIds.join(",")}`
        + `&part=contentDetails`
        + `&key=${Config.youtube_api}`;
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`YouTube API detail query failed with status code ${response.status}`);
    }
    // Parse results
    const detailedJson = await response.json();
    // Detailed results go into an object for keyed lookup
    let detailedResults = {};
    for (let item of detailedJson.items) {
        detailedResults[item.id] = parseYoutubeTime(item.contentDetails.duration);
    }
    // Return detailed results with added video durations
    return results.map(result => {
        if (result.id in detailedResults) {
            return new Result(
                result.id,
                result.thumbnail,
                result.title,
                result.type,
                detailedResults[result.id]
            );
        }
        return result;
    });
}

export function parseYoutubeTime(time) {
    let duration = 0;
    let regex = /(\d+)(H|M|S)/g;
    let match = null;
    while ((match = regex.exec(time))) {
        switch(match[2]) {
            case "H":
                duration += parseInt(match[1]) * 60 * 60;
                break;
            case "M":
                duration += parseInt(match[1]) * 60;
                break;
            case "S":
                duration += parseInt(match[1]);
                break;
        }
    }
    return duration;
}
