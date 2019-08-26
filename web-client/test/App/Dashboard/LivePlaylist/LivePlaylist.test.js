// --- LivePlaylist.test.js ----------------------------------------------------
// Test suite for LivePlaylist.js

import LivePlaylist from "components/App/Dashboard/LivePlaylist/LivePlaylist";
import * as Message from "utils/Message";

import React from "react";
import {render, fireEvent} from "@testing-library/react";
import MockWebSocket from "WebSocket.mock";

function makeTrack(id) {
    return {
        id: id,
        title: `Track Title ${id}`,
        url: `http://example.com/${id}`,
        duration: 0,
        offset: 0,
        live: true,
        thumbnail: `http://example.com/image${id}.png`
    };
}

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

test("requests play queue and status", () => {
    render(<LivePlaylist eventDispatcher={eventDispatcher} socket={socket}/>);
    expect(socket.send).toBeCalledWith(new Message.PlayQueueGetMessage().str());
    expect(socket.send).toBeCalledWith(new Message.PlayStatusGetMessage().str());
});

test("has 2 track list items", () => {
    const {container} = render(<LivePlaylist eventDispatcher={eventDispatcher} socket={socket}/>);
    eventDispatcher.dispatch(new Message.PlayQueueSendMessage([makeTrack("1"), makeTrack("2")]));
    const items = container.querySelectorAll(".LivePlaylist-Track");
    expect(items.length).toBe(2);
});

test("displays track metadata", () => {
    const {container} = render(<LivePlaylist eventDispatcher={eventDispatcher} socket={socket}/>);
    const track = makeTrack("1");
    eventDispatcher.dispatch(new Message.PlayQueueSendMessage([track]));
    const trackNode = container.querySelector(".LivePlaylist-Track");

    expect(track.live).toBe(true);
    expect(trackNode.querySelector(".TrackDuration").textContent).toBe("Live");
    expect(trackNode.querySelector(".TrackTitle").textContent).toBe(track.title);
    expect(trackNode.querySelector("a").href).toBe(track.url);
    expect(trackNode.querySelector("img").src).toBe(track.thumbnail);
});

test("remove track button", () => {
    const {container} = render(<LivePlaylist eventDispatcher={eventDispatcher} socket={socket}/>);
    const tracks = [makeTrack("1"), makeTrack("2")];
    eventDispatcher.dispatch(new Message.PlayQueueSendMessage(tracks));
    const items = container.querySelectorAll(".LivePlaylist-Track");

    fireEvent.click(items[1].querySelector("button"));
    expect(socket.send).toHaveBeenLastCalledWith(
        new Message.PlayQueueRemoveMessage(tracks[1].id).str()
    );
});
