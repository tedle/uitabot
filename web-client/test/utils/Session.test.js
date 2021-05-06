// --- Session.test.js ---------------------------------------------------------
// Test suite for Session.js

import * as Session from "utils/Session";

const session = {handle: "1", secret: "1a1a1a1a1a1a"};

afterEach(() => {
    Session.logout();
    jest.restoreAllMocks();
});

test("session is stored and loaded", () => {
    expect(Session.load()).toBeNull();
    Session.store(session);
    expect(Session.load()).toEqual(session);
});

test("logout removes session", () => {
    Session.store(session);
    expect(Session.load()).toEqual(session);

    Session.logout();
    expect(Session.load()).toBeNull();
});

test("logout redirects to base path", () => {
    delete window.location;
    window.location = { assign: jest.fn() };

    Session.logout();
    expect(window.location.assign).toHaveBeenCalledWith("/");
});
