// --- VoiceChannelSelect.test.js ----------------------------------------------
// Test suite for VoiceChannelSelect.js

import VoiceChannelSelect from "components/App/Dashboard/VoiceChannelSelect/VoiceChannelSelect";
import * as DiscordApi from "utils/DiscordApi";
import * as Message from "utils/Message";

import React from "react";
import {render, fireEvent} from "@testing-library/react";
import MockWebSocket from "WebSocket.mock";

function makeChannel(id, category) {
    let type = (category === null) ?
        DiscordApi.ChannelType.GUILD_CATEGORY : DiscordApi.ChannelType.GUILD_VOICE;
    return {
        id: `${id}`,
        name: (category === null) ? `Category ${id}` : `Channel ${id}`,
        category: (category === null) ? null : `${category}`,
        type: type,
        position: id
    };
}

// First channel is the category, the rest point to it
const channels = [
    makeChannel(1, null),
    makeChannel(2, 1),
    makeChannel(3, 1)
];

let eventDispatcher = null;
let socket = null;

beforeEach(() => {
    eventDispatcher = new Message.EventDispatcher();
    socket = new MockWebSocket("ws://localhost");
});

afterEach(() => {
    eventDispatcher = null;
    socket = null;
});

test("channel list send messages update display", () => {
    const {container, getByText} = render(
        <VoiceChannelSelect eventDispatcher={eventDispatcher} socket={socket}/>
    );

    expect(container.firstChild.children.length).toBe(0);

    eventDispatcher.dispatch(new Message.ChannelListSendMessage(channels));
    expect(container.firstChild.children.length).toBe(1);

    for(let channel of channels) {
        expect(getByText(channel.name)).toBeDefined();
    }
});

test("join channel button sends request", () => {
    const {getByText} = render(
        <VoiceChannelSelect eventDispatcher={eventDispatcher} socket={socket}/>
    );
    eventDispatcher.dispatch(new Message.ChannelListSendMessage(channels));

    const joinableChannel = channels[1];
    expect(joinableChannel.category).not.toBeNull();

    fireEvent.click(getByText(joinableChannel.name));
    expect(socket.send)
        .toHaveBeenLastCalledWith(new Message.ChannelJoinMessage(joinableChannel.id).str());
});

test("disconnect button sends request", () => {
    const {container} = render(
        <VoiceChannelSelect eventDispatcher={eventDispatcher} socket={socket}/>
    );
    eventDispatcher.dispatch(new Message.ChannelListSendMessage(channels));

    const activeChannel = channels[1];
    expect(activeChannel.category).not.toBeNull();

    eventDispatcher.dispatch(new Message.ChannelActiveSendMessage(activeChannel));

    fireEvent.click(container.querySelector(".Disconnect button"));
    expect(socket.send).toHaveBeenLastCalledWith(new Message.ChannelLeaveMessage().str());
});

test("disconnect button appears with active channel", () => {
    const {container} = render(
        <VoiceChannelSelect eventDispatcher={eventDispatcher} socket={socket}/>
    );
    eventDispatcher.dispatch(new Message.ChannelListSendMessage(channels));

    const activeChannel = channels[1];
    expect(activeChannel.category).not.toBeNull();

    expect(container.querySelector(".Active")).toBeNull();
    expect(container.querySelector(".Disconnect")).toBeNull();

    eventDispatcher.dispatch(new Message.ChannelActiveSendMessage(activeChannel));
    expect(container.querySelector(".Active").textContent).toBe(activeChannel.name);
    expect(container.querySelector(".Disconnect")).not.toBeNull();

    eventDispatcher.dispatch(new Message.ChannelActiveSendMessage(null));
    expect(container.querySelector(".Active")).toBeNull();
    expect(container.querySelector(".Disconnect")).toBeNull();
});

test("category button hides channels", () => {
    const {container, getByText} = render(
        <VoiceChannelSelect eventDispatcher={eventDispatcher} socket={socket}/>
    );
    eventDispatcher.dispatch(new Message.ChannelListSendMessage(channels));

    const category = channels[0];
    expect(category.category).toBeNull();

    expect(container.querySelector(".Hidden")).toBeNull();
    fireEvent.click(getByText(category.name));
    expect(container.querySelector(".Hidden")).toBeTruthy();
});
