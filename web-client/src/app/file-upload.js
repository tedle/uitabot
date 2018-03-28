// --- file-upload.js ----------------------------------------------------------
// Component for drag and drop file uploads via websocket

import React from "react";
import * as Message from "./message.js";

export default class FileUploadDropZone extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
        };
    }

    handleFileDrop(e) {
        e.preventDefault();
        for (let file of e.dataTransfer.files) {
            // Only upload files that have an audio/* mime type
            if (RegExp("^audio\\/").test(file.type)) {
                console.log(file);
            }
        }
    }

    handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = "none";
        // Only allow drop payloads with an item that has an audio/* mime type
        for (let item of e.dataTransfer.items) {
            if (RegExp("^audio\\/").test(item.type)) {
                e.dataTransfer.dropEffect = "copy";
                break;
            }
        }
    }

    render() {
        return (
            <div
                onDrop={(e) => this.handleFileDrop(e)}
                onDragOver={(e) => this.handleDragOver(e)}
                onDragEnter={() => console.log("onDragEnter")}
            >
                <p>file drop zone</p>
            </div>
        );
    }
}
