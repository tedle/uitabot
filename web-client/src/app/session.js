import Cookie from "js-cookie";

export function store(session) {
    Cookie.set("session", {id: session.id, name: session.name});
}

export function load() {
    let session = Cookie.getJSON("session");
    if (typeof session === "undefined") {
        return null;
    }
    return session;
}
