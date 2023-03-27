// --- DiscordApi.test.js ------------------------------------------------------
// Test suite for DiscordApi.js

import * as DiscordApi from "utils/DiscordApi";

import Cookie from "js-cookie";
import * as QueryString from "query-string";

beforeEach(() => {
    // Weird that there isn't a clean way to reset the document cookie
    for (let cookie of document.cookie.split(";")) {
        Cookie.remove(cookie.split("=")[0]);
    }
});

test("OAuth URLs match official API spec", () => {
    const clientId = "1a1a1a1a1a";
    const redirectUrl = "http://example.com/";
    const oauthUrl = DiscordApi.createOauthUrl(clientId, redirectUrl);
    const parsed = QueryString.parseUrl(oauthUrl, {decode: false});

    // Spec defined here:
    // https://discord.com/developers/docs/topics/oauth2
    expect(parsed.url).toBe("https://discord.com/api/oauth2/authorize");
    expect(parsed.query.client_id).toBe(clientId);
    expect(parsed.query.redirect_uri).toBe(encodeURIComponent(redirectUrl));
    expect(parsed.query.response_type).toBe("code");
    expect(parsed.query.scope).toBe("identify");
    expect(DiscordApi.verifyState(parsed.query.state)).toBe(true);
    expect(Object.keys(parsed.query).length).toBe(5);
});

test("state verification only matches created state", () => {
    const badState = "1a1a1a1a";
    expect(DiscordApi.verifyState(badState)).toBe(false);

    const goodState = DiscordApi.createState();
    expect(DiscordApi.verifyState(badState)).toBe(false);
    expect(DiscordApi.verifyState(goodState)).toBe(true);
});

test("created state invalidates old state", () => {
    const oldState = DiscordApi.createState();
    expect(DiscordApi.verifyState(oldState)).toBe(true);

    const newState = DiscordApi.createState();
    expect(DiscordApi.verifyState(oldState)).toBe(false);
    expect(DiscordApi.verifyState(newState)).toBe(true);
});

test("created state is random", () => {
    const states = new Array(100).fill(0).map(() => DiscordApi.createState());
    const uniqueStates = new Set(states);
    expect(states.length).toBe(uniqueStates.size);
});
