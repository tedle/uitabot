import Cookie from "js-cookie";

export function store(session) {
    Cookie.set("session", {handle: session.handle, secret: session.secret});
}

export function load() {
    let session = Cookie.getJSON("session");
    if (typeof session === "undefined") {
        return null;
    }
    return session;
}
