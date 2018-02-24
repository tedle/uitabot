import Cookie from "js-cookie";

export function createOauthUrl(clientId, redirectUrl) {
    const encodedUrl = encodeURIComponent(redirectUrl);
    const scope = encodeURIComponent("identify guilds");
    return "https://discordapp.com/api/oauth2/authorize"
        + `?client_id=${clientId}`
        + `&redirect_uri=${encodedUrl}`
        + `&state=${createState()}`
        + "&response_type=code"
        + `&scope=${scope}`;
}

export function createState() {
    let byteArray = new Uint8Array(32);
    window.crypto.getRandomValues(byteArray);
    let state = String();
    for (let byte of byteArray) {
        state += byte.toString(16);
    }
    Cookie.set("state", state);
    return state;
}

export function verifyState(state) {
    let stored_state = Cookie.getJSON("state");
    if (typeof stored_state === "undefined") {
        return false;
    }
    return state === stored_state;
}
