// --- SearchBox.test.js -------------------------------------------------------
// Test suite for SearchBox.js

import SearchBox from "components/App/Dashboard/SearchBox/SearchBox";
import * as Message from "utils/Message";
import * as Youtube from "utils/YoutubeApi";

import React from "react";
import {render, fireEvent, waitForElement} from "@testing-library/react";
import MockWebSocket from "WebSocket.mock";

function fireEventSearch(container, text) {
    const input = container.querySelector("input[type='text']");
    fireEvent.change(input, {target: {value: text}});
    fireEvent.keyDown(input, {key: "Enter", keyCode: 13});
}

function makeResult(id, detailed) {
    return new Youtube.Result(
        `${id}`, `http://example.com/image${id}.png`,
        `Title ${id}`, Youtube.ResultType.VIDEO, detailed ? 60 : null
    );
}

let eventDispatcher = null;
let socket = null;
const results = [1, 2, 3, 4, 5].map(i => makeResult(i, false));
const detailedResults = [1, 2, 3, 4, 5].map(i => makeResult(i, true));

beforeEach(() => {
    eventDispatcher = new Message.EventDispatcher();
    socket = new MockWebSocket("ws://localhost");
    jest.spyOn(Youtube, "search").mockImplementation(async () => results);
    jest.spyOn(Youtube, "searchDetails").mockImplementation(async () => detailedResults);
});

afterEach(() => {
    eventDispatcher = null;
    socket = null;
    jest.restoreAllMocks();
});

test("input box query/url parsing", async () => {
    const {container} = render(<SearchBox eventDispatcher={eventDispatcher} socket={socket}/>);

    const query = "Test input";
    fireEventSearch(container, query);
    expect(Youtube.search).toHaveBeenLastCalledWith(query);

    const url = "http://example.com/track.ogg";
    fireEventSearch(container, url);
    expect(socket.send).toHaveBeenLastCalledWith(new Message.PlayURLMessage(url).str());
});

test("play search result urls", async () => {
    const {container} = render(<SearchBox eventDispatcher={eventDispatcher} socket={socket}/>);
    fireEventSearch(container, "Test input");

    const ul = await waitForElement(() => container.querySelector(".SearchBox-Results ul"));
    expect(ul.children.length).toBe(results.length);

    for(let i = 0; i < results.length; i++) {
        fireEvent.click(ul.children[i].querySelector("button"));
        expect(socket.send)
            .toHaveBeenLastCalledWith(new Message.PlayURLMessage(results[i].url).str());
    }
});

test("search results box is shown immediately", async () => {
    // Youtube.search hangs forever while we test that the search results box appears
    jest.spyOn(Youtube, "search").mockImplementation(async () => {
        await new Promise(() => {});
    });
    const {container} = render(<SearchBox eventDispatcher={eventDispatcher} socket={socket}/>);
    fireEventSearch(container, "Test input");

    await waitForElement(() => container.querySelector(".SearchBox-Results .Loading"));
});

test("simple results are shown quickly", async () => {
    // Youtube.searchDetails hangs forever while we test that non-detailed results are shown
    jest.spyOn(Youtube, "searchDetails").mockImplementation(async () => {
        await new Promise(() => {});
    });
    const {container} = render(<SearchBox eventDispatcher={eventDispatcher} socket={socket}/>);
    fireEventSearch(container, "Test input");

    const ul = await waitForElement(() => container.querySelector(".SearchBox-Results ul"));
    expect(ul.children.length).toBe(results.length);
    // Duration is exclusive to detailed results
    expect(ul.firstChild.querySelector(".Duration").textContent).toBe("");
});

test("detailed results are shown eventually", async () => {
    const {container} = render(<SearchBox eventDispatcher={eventDispatcher} socket={socket}/>);
    fireEventSearch(container, "Test input");

    const ul = await waitForElement(() => {
        let node = container.querySelector(".SearchBox-Results ul");
        // Duration is exclusive to detailed results
        expect(node.firstChild.querySelector(".Duration").textContent).not.toBe("");
        return node;
    });
    expect(ul.children.length).toBe(results.length);
    expect(ul.firstChild.querySelector(".Duration").textContent)
        .toBe(detailedResults[0].displayDuration());
});
