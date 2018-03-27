// --- youtube-api.js ----------------------------------------------------------
// YouTube API request functions

import * as Config from "config";

export function search(query) {
    let url = `https://www.googleapis.com/youtube/v3/search/?`
        + `q=${encodeURI(query)}`
        + `&maxResults=5`
        + `&part=snippet`
        + `&key=${Config.youtube_api}`;
    return fetch(url);
}

export function urlFromId(id) {
    return `https://youtube.com/watch?v=${id}`;
}
