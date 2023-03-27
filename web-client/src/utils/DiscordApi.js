// --- DiscordApi.js -----------------------------------------------------------
// Utility functions for interfacing with Discord API

import Cookie from "js-cookie";
import RandomString from "utils/RandomString";

export var ChannelType = {
    GUILD_TEXT: 0,
    DM: 1,
    GUILD_VOICE: 2,
    GROUP_DM: 3,
    GUILD_CATEGORY: 4,
    GUILD_NEWS: 5,
    GUILD_STORE: 6
};
Object.freeze(ChannelType);

// Generates a "login" URL based on config.json and Discord requirements
export function createOauthUrl(clientId, redirectUrl) {
    const encodedUrl = encodeURIComponent(redirectUrl);
    const scope = encodeURIComponent("identify");
    return "https://discord.com/api/oauth2/authorize"
        // Identifies our app to Discord
        + `?client_id=${clientId}`
        // URI that Discord redirects to after authentication (this site)
        + `&redirect_uri=${encodedUrl}`
        // Unique, random state that we generated to prevent CSRF
        + `&state=${createState()}`
        // Requesting an auth code to pass to the backend, which will be turned into a token
        + "&response_type=code"
        // Permissions we're requesting of the user
        + `&scope=${scope}`;
}

// Generate a long, cryptographically random string and store it in a cookie
// This will be sent to the Discord API and then passed back to us to verify
export function createState() {
    let state = RandomString(64);
    Cookie.set("state", state);
    return state;
}

// Validates the state parameter returned by Discord with what we have stored
export function verifyState(state) {
    let stored_state = Cookie.getJSON("state");
    if (typeof stored_state === "undefined") {
        return false;
    }
    return state === stored_state;
}
