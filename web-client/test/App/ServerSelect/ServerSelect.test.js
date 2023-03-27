// --- ServerSelect.test.js ----------------------------------------------------
// Test suite for ServerSelect.js

import ServerSelect from "components/App/ServerSelect/ServerSelect";
import * as Message from "utils/Message";
import * as Session from "utils/Session";

import React from "react";
import {render, fireEvent} from "@testing-library/react";
import MockWebSocket from "WebSocket.mock";

let eventDispatcher = null;
let socket = null;
const servers = [1, 2, 3, 4, 5].map(i => ({
    id: `${i}`,
    name: `Server ${i}`,
    icon: null
}));

beforeEach(() => {
    eventDispatcher = new Message.EventDispatcher();
    socket = new MockWebSocket("ws://localhost");
});

afterEach(() => {
    eventDispatcher = null;
    socket = null;
});

test("server list renders as empty without input", () => {
    const {getByText} = render(
        <ServerSelect
            eventDispatcher={eventDispatcher}
            socket={socket}
            onServerSelect={jest.fn()}
        />
    );

    expect(getByText(/no servers/i)).toBeDefined();
});

test("server list renders as empty with an empty list", () => {
    const {getByText} = render(
        <ServerSelect
            eventDispatcher={eventDispatcher}
            socket={socket}
            onServerSelect={jest.fn()}
        />
    );

    expect(socket.send).toHaveBeenCalledWith(new Message.ServerListGetMessage().str());
    eventDispatcher.dispatch(new Message.ServerListSendMessage([]));

    expect(getByText(/no servers/i)).toBeDefined();
});

test("server list renders a given list", () => {
    const {container, getByText} = render(
        <ServerSelect
            eventDispatcher={eventDispatcher}
            socket={socket}
            onServerSelect={jest.fn()}
        />
    );

    expect(socket.send).toHaveBeenCalledWith(new Message.ServerListGetMessage().str());
    eventDispatcher.dispatch(new Message.ServerListSendMessage(servers));

    expect(container.querySelectorAll("li").length).toBe(servers.length);

    for (const server of servers) {
        expect(getByText(server.name)).toBeDefined();
    }
});

test("server list renders given and default icons", () => {
    const {container} = render(
        <ServerSelect
            eventDispatcher={eventDispatcher}
            socket={socket}
            onServerSelect={jest.fn()}
        />
    );

    const noIconServer = {
        id: "1",
        name: "Server 1",
        icon: null
    };
    const iconServer = {
        id: "2",
        name: "Server 2",
        icon: "IcOnHaSh"
    };

    eventDispatcher.dispatch(new Message.ServerListSendMessage([noIconServer]));
    expect(container.querySelector("li .NullLogo"))
        .not.toBeNull();

    eventDispatcher.dispatch(new Message.ServerListSendMessage([iconServer]));
    expect(container.querySelector("li img").src)
        .toBe("http://localhost/" + iconServer.icon);
});

test("onServerSelect callbacks are triggered", () => {
    const onSelect = jest.fn();
    const {getByText} = render(
        <ServerSelect
            eventDispatcher={eventDispatcher}
            socket={socket}
            onServerSelect={onSelect}
        />
    );

    expect(socket.send).toHaveBeenCalledWith(new Message.ServerListGetMessage().str());
    eventDispatcher.dispatch(new Message.ServerListSendMessage(servers));

    for (const server of servers) {
        fireEvent.click(getByText(server.name));
        expect(onSelect).toHaveBeenLastCalledWith(server);
    }
});

test("logout button deletes session", () => {
    jest.spyOn(Session, "logout");
    const {getByText} = render(
        <ServerSelect
            eventDispatcher={eventDispatcher}
            socket={socket}
            onServerSelect={jest.fn()}
        />
    );

    expect(Session.logout).not.toHaveBeenCalled();
    fireEvent.click(getByText(/logout/i));
    expect(Session.logout).toHaveBeenCalled();
});
