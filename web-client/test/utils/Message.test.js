// --- Message.test.js ---------------------------------------------------------
// Test suite for Message.js

import * as Message from "utils/Message";

const mockServerId = "1a1a1a1a1a";
const mockMessage = `{"header":"server.join","server_id":"${mockServerId}"}`;

test("messages serialize to JSON", () => {
    const message = new Message.ServerJoinMessage(mockServerId);
    expect(message.str()).toBe(mockMessage);
});

test("event dispatcher triggers callbacks", () => {
    const dispatcher = new Message.EventDispatcher();
    const callback = jest.fn();

    dispatcher.setMessageHandler("server.join", callback);
    dispatcher.dispatch(Message.parse(mockMessage));
    expect(callback.mock.calls.length).toBe(1);
    expect(callback).toHaveBeenCalledWith(new Message.ServerJoinMessage(mockServerId));

    dispatcher.clearMessageHandler("server.join");
    dispatcher.dispatch(Message.parse(mockMessage));
    expect(callback.mock.calls.length).toBe(1);
});

test("event dispatcher requires messages for dispatch", () => {
    const dispatcher = new Message.EventDispatcher();

    expect(() => dispatcher.dispatch(mockMessage)).toThrow(TypeError);
    expect(() => dispatcher.dispatch(Message.parse(mockMessage))).not.toThrow();
});

test("parse forwards object parameters", () => {
    const message = Message.parse(mockMessage);
    expect(message instanceof Message.ServerJoinMessage).toBe(true);
    expect(message.server_id).toBe(mockServerId);
});

test("parse throws on invalid object parameters", () => {
    const incorrectFieldName = () => Message.parse(`{"header":"server.join","server_name":"Name"}`);
    expect(incorrectFieldName).toThrow(TypeError);
    const missingParams = () => Message.parse(`{"header":"server.join"}`);
    expect(missingParams).toThrow(TypeError);
});
