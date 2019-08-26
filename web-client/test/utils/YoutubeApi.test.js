// --- YoutubeApi.test.js ------------------------------------------------------
// Test suite for YoutubeApi.js

import * as Youtube from "utils/YoutubeApi";

import * as Config from "config";
import * as QueryString from "query-string";
import mockSearchJson from "youtube-search.mock.json";
import mockDetailsJson from "youtube-details.mock.json";

const m = s => s * 60;
const h = s => s * 60 * 60;

const id = "1y2o3u4t5u6b7e";
const thumbnail = `http://example.com/${id}.png`;
const title = "Video Title";
const duration = 60;

// In case jsdom adds fetch support later
expect(global.fetch).not.toBeDefined();
global.fetch = jest.fn();

afterEach(() => {
    global.fetch.mockReset();
});

test("search throws on bad response code", async () => {
    fetch.mockReturnValue({ok: false, status: 403});
    await expect(Youtube.search("search")).rejects.toThrow();
});

test("search throws on unknown video type", async () => {
    const jsonClone = JSON.parse(JSON.stringify(mockSearchJson));
    jsonClone.items[0].id.kind = "youtube#unknown";
    fetch.mockReturnValue({ok: true, status: 200});
    await expect(Youtube.search("search")).rejects.toThrow();
});

test("search returns correct results", async () => {
    fetch.mockReturnValue({ok: true, status: 200, json: () => mockSearchJson});
    const results = await Youtube.search("search");
    for (let i of results.keys()) {
        if (mockSearchJson.items[i].snippet.liveBroadcastContent == "live") {
            expect(results[i].type).toBe(Youtube.ResultType.LIVE);
        }
        else if (mockSearchJson.items[i].id.kind == "youtube#video") {
            expect(results[i].type).toBe(Youtube.ResultType.VIDEO);
        }
        else if (mockSearchJson.items[i].id.kind == "youtube#playlist") {
            expect(results[i].type).toBe(Youtube.ResultType.PLAYLIST);
        }
        else {
            throw Error("Did not detect video type properly");
        }
        expect(results[i].title).toBe(mockSearchJson.items[i].snippet.title);
        expect(results[i].thumbnail).toBe(mockSearchJson.items[i].snippet.thumbnails.medium.url);
        expect(results[i].duration).toBeNull();
        expect(results[i].id)
            .toBe(mockSearchJson.items[i].id.videoId || mockSearchJson.items[i].id.playlistId);
    }
});

test("search details throws on bad response code", async () => {
    fetch.mockReturnValueOnce({ok: true, status: 200, json: () => mockSearchJson})
        .mockReturnValueOnce({ok: false, status: 403});
    const results = await Youtube.search("search");
    await expect(Youtube.searchDetails(results)).rejects.toThrow();
});

test("search details returns correct results", async () => {
    fetch.mockReturnValueOnce({ok: true, status: 200, json: () => mockSearchJson})
        .mockReturnValueOnce({ok: true, status: 200, json: () => mockDetailsJson});
    const results = await Youtube.search("search");
    const details = await Youtube.searchDetails(results);

    expect(results.length).toBe(details.length);

    for (let i of results.keys()) {
        expect(details[i].id).toBe(results[i].id);
        expect(details[i].thumbnail).toBe(results[i].thumbnail);
        expect(details[i].title).toBe(results[i].title);
        expect(details[i].type).toBe(results[i].type);
        if (results[i].type == Youtube.ResultType.VIDEO) {
            expect(details[i].duration).toBe(60);
        }
        else {
            expect(details[i].duration).toBeNull;
        }
    }
});

test("queries are formatted properly", async () => {
    fetch.mockReturnValueOnce({ok: true, status: 200, json: () => mockSearchJson})
        .mockReturnValueOnce({ok: true, status: 200, json: () => mockDetailsJson});
    const query = ":search!with@symbols:";
    const results = await Youtube.search(query);
    await Youtube.searchDetails(results);

    expect(fetch.mock.calls.length).toBe(2);
    const searchQuery = QueryString.parseUrl(fetch.mock.calls[0][0], {decode: false});
    const detailsQuery = QueryString.parseUrl(fetch.mock.calls[1][0], {decode: false});
    const videoList = results.filter(r => r.type == Youtube.ResultType.VIDEO).map(r => r.id);

    expect(searchQuery.url).toBe("https://www.googleapis.com/youtube/v3/search/");
    expect(searchQuery.query.q).toBe(encodeURI(query));
    expect(searchQuery.query.maxResults).toBe("10");
    expect(searchQuery.query.part).toBe("snippet");
    expect(searchQuery.query.type).toBe("video,playlist");
    expect(searchQuery.query.key).toBe(Config.youtube_api);

    expect(detailsQuery.url).toBe("https://www.googleapis.com/youtube/v3/videos/");
    expect(detailsQuery.query.id).toBe(videoList.join(","));
    expect(detailsQuery.query.part).toBe("contentDetails");
    expect(detailsQuery.query.key).toBe(Config.youtube_api);
});

test("results are correctly formatted", () => {
    const video = new Youtube.Result(id, thumbnail, title, Youtube.ResultType.VIDEO, duration);
    const stream = new Youtube.Result(id, thumbnail, title, Youtube.ResultType.LIVE, duration);
    const list = new Youtube.Result(id, thumbnail, title, Youtube.ResultType.PLAYLIST, duration);
    const nullVideo = new Youtube.Result(id, thumbnail, title, Youtube.ResultType.VIDEO, null);

    expect(video.id).toBe(id);
    expect(video.thumbnail).toBe(thumbnail);
    expect(video.title).toBe(title);
    expect(video.duration).toBe(duration);

    expect(video.url).toBe(`https://youtube.com/watch?v=${id}`);
    expect(stream.url).toBe(`https://youtube.com/watch?v=${id}`);
    expect(list.url).toBe(`https://youtube.com/playlist?list=${id}`);

    expect(video.displayDuration()).toBe("1:00");
    expect(stream.displayDuration()).toBe("Live");
    expect(list.displayDuration()).toBe("Playlist");
    expect(nullVideo.displayDuration()).toBe("");
});

test("timestamps are correctly parsed", () => {
    expect(Youtube.parseYoutubeTime("PT5S"    )).toBe(h(0) + m(0) + 5);
    expect(Youtube.parseYoutubeTime("PT5M5S"  )).toBe(h(0) + m(5) + 5);
    expect(Youtube.parseYoutubeTime("PT1H0M0S")).toBe(h(1) + m(0) + 0);
    expect(Youtube.parseYoutubeTime("PT1H1M1S")).toBe(h(1) + m(1) + 1);
    expect(Youtube.parseYoutubeTime("PT10H1S" )).toBe(h(10)+ m(0) + 1);
});
