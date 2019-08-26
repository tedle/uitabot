// --- App.test.js -------------------------------------------------------------
// Test suite for App.js

import App from "components/App/App";
import * as Message from "utils/Message";
import * as Session from "utils/Session";

import React from "react";
import {render, fireEvent, waitForElementToBeRemoved} from "@testing-library/react";
import MockWebSocket from "WebSocket.mock";

global.WebSocket = MockWebSocket;

const session = {handle: "1", secret: "1a1a1a1a1a"};
const user = {id: "2", name: "User 2"};
const server = {id: "3", name: "Server 3"};

function authenticate(socket) {
    Session.store(session);

    socket.readyState = WebSocket.OPEN;
    socket.onopen();
    expect(socket.send)
        .toHaveBeenCalledWith(new Message.AuthSessionMessage(session.handle, session.secret).str());

    socket.onmessage({data: new Message.AuthSucceedMessage(user, session).str()});
}

afterEach(() => {
    jest.useRealTimers();
    Session.logout();
});

test("shows initial attempted connection", () => {
    const {container} = render(<App/>);

    expect(container.textContent).toMatch(/connecting/i);
});

test("shows failed connection", () => {
    const {container} = render(<App/>);

    MockWebSocket.instance.onclose();
    expect(container.textContent).toMatch(/connection error/i);
});

test("shows login dialog without a stored session", () => {
    const {container} = render(<App/>);

    MockWebSocket.instance.onopen();
    expect(container.textContent).toMatch(/login/i);
});

test("shows login dialog with an invalid session", () => {
    const {container} = render(<App/>);
    const socket = MockWebSocket.instance;
    Session.store({handle: null, secret: null});

    socket.readyState = WebSocket.OPEN;
    socket.onopen();
    expect(container.textContent).toMatch(/authenticating/i);

    socket.onmessage({data: new Message.AuthFailMessage().str()});
    expect(container.textContent).toMatch(/login/i);
});

test("shows server select after authentication", () => {
    const {container} = render(<App/>);

    authenticate(MockWebSocket.instance);
    expect(container.textContent).toMatch(/future server/i);
});

test("shows dashboard after selecting a server", () => {
    const {container, getByText} = render(<App/>);
    const socket = MockWebSocket.instance;

    authenticate(socket);

    expect(socket.send).toHaveBeenCalledWith(new Message.ServerListGetMessage().str());
    socket.onmessage({data: new Message.ServerListSendMessage([server]).str()});
    fireEvent.click(getByText(server.name));

    expect(socket.send).toHaveBeenCalledWith(new Message.ServerJoinMessage(server.id).str());
    expect(container.querySelector(".Dashboard")).not.toBeNull();
});

test("shows errors", () => {
    const {container, getByText} = render(<App/>);
    const socket = MockWebSocket.instance;

    authenticate(socket);
    socket.onmessage({data: new Message.ServerListSendMessage([server]).str()});
    fireEvent.click(getByText(server.name));

    expect(container.querySelector(".Dashboard")).not.toBeNull();

    socket.onmessage({data: new Message.ErrorUrlInvalidMessage().str()});
    socket.onmessage({data: new Message.ErrorUrlInvalidMessage().str()});
    socket.onmessage({data: new Message.ErrorUrlInvalidMessage().str()});
    expect(container.querySelectorAll(".Errors-List-Item").length).toBe(3);
});

test("removes error when clicked", async () => {
    const {container, getByText} = render(<App/>);
    const socket = MockWebSocket.instance;

    authenticate(socket);
    socket.onmessage({data: new Message.ServerListSendMessage([server]).str()});
    fireEvent.click(getByText(server.name));

    expect(container.querySelector(".Dashboard")).not.toBeNull();
    socket.onmessage({data: new Message.ErrorUrlInvalidMessage().str()});

    const button = container.querySelector(".Errors-List-Item button");
    expect(button).not.toBeNull();
    fireEvent.click(button);

    await waitForElementToBeRemoved(() => container.querySelector(".Errors-List-Item"));
});

test("removes error after timeout", () => {
    jest.useFakeTimers();

    const {container, getByText} = render(<App/>);
    const socket = MockWebSocket.instance;

    authenticate(socket);
    socket.onmessage({data: new Message.ServerListSendMessage([server]).str()});
    fireEvent.click(getByText(server.name));

    expect(container.querySelector(".Dashboard")).not.toBeNull();
    socket.onmessage({data: new Message.ErrorUrlInvalidMessage().str()});

    expect(container.querySelector(".Errors-List-Item")).not.toBeNull();
    jest.advanceTimersByTime(10000);
    expect(container.querySelector(".Errors-List-Item")).toBeNull();
});

test("active error messages won't throw on unmount", () => {
    jest.useFakeTimers();

    const {container, getByText, unmount} = render(<App/>);
    const socket = MockWebSocket.instance;

    authenticate(socket);
    socket.onmessage({data: new Message.ServerListSendMessage([server]).str()});
    fireEvent.click(getByText(server.name));

    expect(container.querySelector(".Dashboard")).not.toBeNull();
    socket.onmessage({data: new Message.ErrorUrlInvalidMessage().str()});

    const button = container.querySelector(".Errors-List-Item button");
    expect(button).not.toBeNull();
    fireEvent.click(button);

    unmount();

    jest.spyOn(global.console, "error").mockImplementation(() => {});
    expect(jest.runAllTimers).not.toThrow();
    expect(console.error).not.toHaveBeenCalled();
    console.error.mockRestore();
});

test("failed WebSocket init shows error", () => {
    const errorMessage = "Failed to create WebSocket";
    const socketMock = jest.spyOn(global, "WebSocket")
        .mockImplementation(() => {throw new Error(errorMessage);});

    const {getByText} = render(<App/>);

    expect(getByText(errorMessage)).toBeDefined();
    socketMock.mockRestore();
});

test("periodically sends heartbeat messages", () => {
    jest.useFakeTimers();

    render(<App/>);
    const socket = MockWebSocket.instance;

    authenticate(socket);

    jest.advanceTimersByTime(1000 * 60 * 15);
    expect(socket.send.mock.calls.filter(m => (
        m[0] == new Message.HeartbeatMessage().str()
    )).length).toBeGreaterThan(10);
});

test("server kick message returns to server select view", () => {
    const {container, getByText} = render(<App/>);
    const socket = MockWebSocket.instance;

    authenticate(socket);

    socket.onmessage({data: new Message.ServerListSendMessage([server]).str()});
    fireEvent.click(getByText(server.name));
    expect(container.querySelector(".Dashboard")).not.toBeNull();

    socket.onmessage({data: new Message.ServerKickMessage().str()});
    expect(container.textContent).toMatch(/future server/i);
});
