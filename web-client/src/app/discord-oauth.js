// --- discord-oauth.js --------------------------------------------------------
// Utility functions for interfacing with Discord OAuth API

import Cookie from "js-cookie";
import * as Utils from "./utils.js";

// Generates a "login" URL based on config.json and Discord requirements
export function createOauthUrl(clientId, redirectUrl) {
    const encodedUrl = encodeURIComponent(redirectUrl);
    const scope = encodeURIComponent("identify");
    return "https://discordapp.com/api/oauth2/authorize"
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
    let state = Utils.randomString(64);
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
