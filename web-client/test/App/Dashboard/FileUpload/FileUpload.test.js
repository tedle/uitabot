// --- FileUpload.test.js ------------------------------------------------------
// Test suite for FileUpload.js

import FileUpload, {FileUploadContext} from "components/App/DashBoard/FileUpload/FileUpload";
import * as Errors from "components/App/Errors/Errors";
import * as Message from "utils/Message";
import * as Session from "utils/Session";

import React from "react";
import {
    render,
    fireEvent,
    wait,
    waitForElement,
    waitForElementToBeRemoved
} from "@testing-library/react";
// Use Simulate instead of fireEvent because jsdom doesn't support dataTransfer events
// https://github.com/jsdom/jsdom/issues/1568
import {Simulate} from "react-dom/test-utils";

const discordServer = {id: "12345"};
const fileData = new Uint8Array(128).map(() => Math.random() * 255);
const file = new File([fileData], "test.ogg", {type: "audio/vorbis"});
const session = {handle: "handle", secret: "secret"};

// Bless this mess, testing long running asynchronous tasks is not pretty
describe("file uploads", () => {
    // Socket to spy on
    let mockSocket = null;

    beforeEach(() => {
        mockSocket = {
            send: jest.fn(),
            close: jest.fn(),
            onopen: null
        };
        jest.spyOn(global, "WebSocket").mockImplementation(() => mockSocket);
        Session.store(session);
    });

    afterEach(() => {
        Session.logout();
        global.WebSocket.mockRestore();
        mockSocket = null;
    });

    async function uploadProtocol(socket) {
        mockSocket.onopen();
        mockSocket.onmessage({data: new Message.AuthSucceedMessage(null, null).str()});
        mockSocket.onmessage({data: new Message.FileUploadStartMessage(fileData.length).str()});
        // Yield control back to the upload task
        await wait();
        mockSocket.onmessage({data: new Message.FileUploadCompleteMessage(fileData.length).str()});
        // Yield control back to the upload task (once for each await)
        await wait();
        await wait();
    }

    async function blobToArray(blob) {
        return new Promise(resolve => {
            let reader = new FileReader();
            reader.onload = e => resolve(new Uint8Array(e.target.result));
            reader.readAsArrayBuffer(blob);
        });
    }

    async function checkResults(mockCalls) {
        const calls = mockSocket.send.mock.calls;
        calls[3][0] = await blobToArray(calls[3][0]);
        const expectedCalls = [
            [new Message.AuthSessionMessage(session.handle, session.secret).str()],
            [new Message.ServerJoinMessage(discordServer.id).str()],
            [new Message.FileUploadStartMessage(fileData.length).str()],
            [fileData]
        ];
        // Simple string comparisons
        expect(calls[0][0]).toBe(expectedCalls[0][0]);
        expect(calls[1][0]).toBe(expectedCalls[1][0]);
        expect(calls[2][0]).toBe(expectedCalls[2][0]);
        // Byte for byte binary comparison
        expect(calls[3][0].every((v, i) => expectedCalls[3][0][i] === v)).toBe(true);
    }

    test("complete dropped upload", async () => {
        const {container} = render(<FileUpload discordServer={discordServer}> </FileUpload>);

        Simulate.dragEnter(container.querySelector(".FileUpload-DropZone"));
        const overlay = await waitForElement(() => container.querySelector(".FileUpload-Overlay"));
        Simulate.drop(overlay, {dataTransfer: {files: [file]}});

        await uploadProtocol(mockSocket);
        await checkResults(mockSocket.send.mock.calls);
    });

    test("complete React context upload", async () => {
        const {getByTestId} = render(
            <FileUpload discordServer={discordServer}>
                <FileUploadContext.Consumer>
                    {upload => <button data-testid="upload" onClick={(e) => upload([file])}/>}
                </FileUploadContext.Consumer>
            </FileUpload>
        );
        fireEvent.click(getByTestId("upload"));

        await uploadProtocol(mockSocket);
        await checkResults(mockSocket.send.mock.calls);
    });
});

test("drop effects change with file type", () => {
    const {container} = render(<FileUpload discordServer={discordServer}> </FileUpload>);
    let mockEvent = {
        dataTransfer: {
            dropEffect: "",
            items: [{type: "application/octet-stream"}]
        }
    };

    // Check drop effect without an audio file
    Simulate.dragOver(container.querySelector(".FileUpload-DropZone"), mockEvent);
    expect(mockEvent.dataTransfer.dropEffect).toBe("none");

    // Check drop effect with an audio file and invalid file
    mockEvent.dataTransfer.items.push({type: "audio/mp3"});
    Simulate.dragOver(container.querySelector(".FileUpload-DropZone"), mockEvent);
    expect(mockEvent.dataTransfer.dropEffect).toBe("copy");

    // Check drop effect with a video file
    mockEvent.dataTransfer.items = [{type: "video/mp4"}];
    Simulate.dragOver(container.querySelector(".FileUpload-DropZone"), mockEvent);
    expect(mockEvent.dataTransfer.dropEffect).toBe("copy");
});

test("overlay appears and disappears when dragging", async () => {
    const {container} = render(<FileUpload discordServer={discordServer}> </FileUpload>);

    expect(container.querySelector(".FileUpload-Overlay")).toBeNull();
    Simulate.dragEnter(container.querySelector(".FileUpload-DropZone"));
    const overlay = await waitForElement(() => container.querySelector(".FileUpload-Overlay"));
    Simulate.dragLeave(overlay);
    await waitForElementToBeRemoved(() => container.querySelector(".FileUpload-Overlay"));
});

test("errors bubble on failure", async () => {
    let sessionError = await new Promise(resolve => {
        const {getByTestId} = render(
            <Errors.Context.Provider value={(error) => resolve(error)}>
                <FileUpload discordServer={discordServer}>
                    <FileUploadContext.Consumer>
                        {upload => <button data-testid="upload" onClick={(e) => upload([file])}/>}
                    </FileUploadContext.Consumer>
                </FileUpload>
            </Errors.Context.Provider>
        );
        const button = getByTestId("upload");
        fireEvent.click(button);
    });
    expect(sessionError).toBe("File upload error: No session cookie");
});
