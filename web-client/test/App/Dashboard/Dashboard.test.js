// --- Dashboard.test.js -------------------------------------------------------
// Test suite for Dashboard.js

import Dashboard from "components/App/Dashboard/Dashboard";
import {EventDispatcher} from "utils/Message";

import React from "react";
import {render, fireEvent} from "@testing-library/react";
import MockWebSocket from "WebSocket.mock";

test("tab clicks will switch views on mobile", () => {
    const eventDispatcher = new EventDispatcher();
    const socket = new MockWebSocket("ws://localhost");

    const {container, getByText} = render(
        <Dashboard
            discordServer={{}} discordUser={{}}
            eventDispatcher={eventDispatcher} socket={socket}
        />
    );

    // Default tab should be playlist
    expect(container.querySelector(".Dashboard-Playlist.hidden-xs")).toBeNull();
    expect(container.querySelector(".Dashboard-VoiceChannel.hidden-xs")).toBeDefined();

    fireEvent.click(getByText(/voice channels/i));
    expect(container.querySelector(".Dashboard-Playlist.hidden-xs")).toBeDefined();
    expect(container.querySelector(".Dashboard-VoiceChannel.hidden-xs")).toBeNull();

    fireEvent.click(getByText(/playlist/i));
    expect(container.querySelector(".Dashboard-Playlist.hidden-xs")).toBeNull();
    expect(container.querySelector(".Dashboard-VoiceChannel.hidden-xs")).toBeDefined();
});
