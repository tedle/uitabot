// --- Authenticate.test.js ----------------------------------------------------
// Test suite for Authenticate.js

import Authenticate from "components/App/Authenticate/Authenticate";
import * as DiscordApi from "utils/DiscordApi";
import * as Message from "utils/Message";
import * as Session from "utils/Session";

import React from "react";
import {render} from "@testing-library/react";
import MockWebSocket from "WebSocket.mock";

// Reminder in case jsdom adds location.assign support
expect(window.location.assign).toThrow();
window.location.assign = jest.fn();

let socket = null;
const onAuthFail = jest.fn();

beforeEach(() => {
    socket = new MockWebSocket("ws://localhost");
    window.history.pushState(null, null, "/");
});

afterEach(() => {
    socket = null;
    onAuthFail.mockClear();
    Session.logout();
});

describe("code authentication", () => {
    const code = "1a1a1a1a1a1a";

    test("attempt authentication when returned auth state is valid", () => {
        const state = DiscordApi.createState();
        window.history.pushState(null, null, `/?code=${code}&state=${state}`);

        render(<Authenticate socket={socket} onAuthFail={onAuthFail}/>);
        expect(socket.send).toHaveBeenLastCalledWith(new Message.AuthCodeMessage(code).str());
        expect(onAuthFail).not.toHaveBeenCalled();

        // Query params should be stripped after OAuth flow
        expect(window.location.search).toBe("");
    });

    test("fail when returned auth state is invalid", () => {
        const state = "2b2b2b2b2b2b";
        window.history.pushState(null, null, `/?code=${code}&state=${state}`);

        render(<Authenticate socket={socket} onAuthFail={onAuthFail}/>);
        expect(socket.send).not.toHaveBeenCalled();
        expect(onAuthFail).toHaveBeenCalled();
    });

    test("fail when there is no returned auth state", () => {
        window.history.pushState(null, null, `/?code=${code}`);

        render(<Authenticate socket={socket} onAuthFail={onAuthFail}/>);
        expect(socket.send).not.toHaveBeenCalled();
        expect(onAuthFail).toHaveBeenCalled();
    });
});

describe("session authentication", () => {
    test("attempt authentication when valid session is stored", () => {
        const session = {handle: "10", secret: "3c3c3c3c3c3c"};
        Session.store(session);
        render(<Authenticate socket={socket} onAuthFail={onAuthFail}/>);
        expect(socket.send).toHaveBeenLastCalledWith(
            new Message.AuthSessionMessage(session.handle, session.secret).str()
        );
    });

    test("fail when no session is stored", () => {
        render(<Authenticate socket={socket} onAuthFail={onAuthFail}/>);
        expect(socket.send).not.toHaveBeenCalled();
        expect(onAuthFail).toHaveBeenCalled();
    });
});
