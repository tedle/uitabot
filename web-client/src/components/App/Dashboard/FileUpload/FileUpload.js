// --- FileUpload.js -----------------------------------------------------------
// Component for drag and drop file uploads via websocket

import "./FileUpload.scss";

import React from "react";
import { CSSTransition } from "react-transition-group";
import * as Config from "config";
import * as Message from "utils/Message";
import * as Session from "utils/Session";

var UploadStatus = {
    QUEUED: 1,
    UPLOADING: 2,
    COMPLETED: 3,
    CANCELLED: 4
}
Object.freeze(UploadStatus);

// Allows nested components to upload files programmatically (upload buttons, etc)
export const FileUploadContext = React.createContext(() => {});

export default class FileUploadDropZone extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            progress: Array(),
            progressIndex: 0,
            showProgress: false
        };
        this._isMounted = false;
    }

    componentDidMount() {
        this._isMounted = true;
    }

    componentWillUnmount() {
        this._isMounted = false;
    }

    handleFileDrop(event) {
        // Prevent default required to stop the browser from opening files in a new tab
        event.preventDefault();
        this.setState({showOverlay: false});
        const files = Array.from(event.dataTransfer.files)
            .filter(file => /^audio\//.test(file.type));
        this.upload(files);
    }

    handleDragOver(event) {
        // Prevent default required to change drop effect
        event.preventDefault();
        event.dataTransfer.dropEffect = "none";
        // Only allow drop payloads with an item that has an audio/* mime type
        for (let item of event.dataTransfer.items) {
            if (/^audio\//.test(item.type)) {
                event.dataTransfer.dropEffect = "copy";
                break;
            }
        }
        if (event.dataTransfer.dropEffect != "copy") {
            this.setState({showOverlay: false});
        }
    }

    async fileSend(file, socket, dispatcher, progressCallback) {
        socket.send(new Message.FileUploadStartMessage(file.size).str());
        // Wait for the server response
        await this.fileReady(dispatcher);
        // Stream the file data in one go
        const chunk_size = 4096;
        let start = 0;
        let end = 0;
        while (end < file.size) {
            start = end;
            end = Math.min(end + chunk_size, file.size);
            socket.send(file.slice(start, end));
        }
        // Wait for the server response
        let interval = setInterval(() => {
            if (!this._isMounted) {
                clearInterval(interval);
                socket.close(1000);
                return;
            }
            progressCallback(socket.bufferedAmount);
        }, 200);
        try {
            await this.fileComplete(dispatcher, socket);
        } finally {
            clearInterval(interval);
        }
    }

    fileReady(dispatcher) {
        // Create an awaitable event that triggers after a server response
        return new Promise((resolve, reject) => {
            dispatcher.setMessageHandler("file.upload.start", m => {
                resolve();
            });
            dispatcher.setMessageHandler("error.file.invalid", m => {
                reject(m.error);
            });
            dispatcher.setMessageHandler("error.queue.full", m => {
                reject("Queue is full");
            });
            setTimeout(() => reject("Server timed out or disconnected"), 5000);
        });
    }

    fileComplete(dispatcher, socket) {
        // Create an awaitable event that triggers after a server response
        return new Promise((resolve, reject) => {
            dispatcher.setMessageHandler("file.upload.complete", m => {
                resolve();
            });
            dispatcher.setMessageHandler("error.file.invalid", m => {
                reject(m.error);
            });
            dispatcher.setMessageHandler("error.queue.full", m => {
                reject("Queue is full");
            });
            let oldBufferedAmount = socket.bufferedAmount;
            let bufferInterval = setInterval(() => {
                if (oldBufferedAmount == socket.bufferedAmount) {
                    clearInterval(bufferInterval);
                    reject("Server timed out or disconnected");
                }
                oldBufferedAmount = socket.bufferedAmount;
            }, 5000);
        });
    }

    upload(files) {
        this.setState({showProgress: false});

        if (files.length == 0) {
            return;
        }
        // Create a new authenticated socket to do the file uploads from asynchronously without
        // jamming up the send buffer queue
        let eventDispatcher = new Message.EventDispatcher();
        let socket = new WebSocket(Config.bot_url);
        try {
            // Load up the stored credentials that absolutely most likely exist
            let session = Session.load();
            if (session === null) {
                throw new Error("No session cookie");
            }
            // Initialize socket callbacks
            socket.onmessage = e => eventDispatcher.dispatch(Message.parse(e.data));
            socket.onerror = e => console.log(e);
            socket.onopen = e => {
                socket.send(new Message.AuthSessionMessage(session.handle, session.secret).str());
            };
            // After authentication, join the selected server and upload the files
            eventDispatcher.setMessageHandler("auth.succeed", async (m) => {
                try {
                    // Select the server to upload files to
                    socket.send(new Message.ServerJoinMessage(this.props.discordServer.id).str());
                    // Organize file data into React consumable state
                    let fileProgress = files.map(file => {
                        return {
                            name: file.name,
                            size: file.size,
                            progress: 0.0,
                            status: UploadStatus.QUEUED,
                            error: ""
                        };
                    });
                    this.setState({progress: fileProgress, progressIndex: 0, showProgress: true})
                    // Iterate over each file and upload it to the server
                    for (let [index, file] of files.entries()) {
                        try {
                            if (socket.readyState != WebSocket.OPEN) {
                                throw new Error("Server disconnected");
                            }
                            this.setState({progressIndex: index});
                            await this.fileSend(file, socket, eventDispatcher, (buffered) => {
                                fileProgress[index].status = UploadStatus.UPLOADING;
                                fileProgress[index].progress = (file.size - buffered) / file.size;
                                this.setState({progress: fileProgress, showProgress: true});
                            });
                            // Check after every control flow yield that is followed by state
                            // changes that we are still mounted.
                            // Sorry for this wild asynchronous mess, I blame sticking to basic
                            // React since it'd be overkill to get a state library for just this
                            // one component... but still...
                            if (!this._isMounted) {
                                socket.close(1000);
                                return;
                            }
                            fileProgress[index].status = UploadStatus.COMPLETED;
                        } catch (error) {
                            fileProgress[index].status = UploadStatus.CANCELLED;
                            fileProgress[index].error = error;
                        } finally {
                            fileProgress[index].progress = 1.0;
                            this.setState({progress: fileProgress, showProgress: true});
                        }
                    }
                } finally {
                    this.setState({showProgress: false});
                    socket.close(1000);
                }
            });
            // There is a very rare chance that the server side credentials have expired and failed to renew
            eventDispatcher.setMessageHandler("auth.fail", m => {
                alert("File upload authentication failed, try refreshing");
                socket.close(1000);
            });
        } catch (error) {
            alert(`Error uploading files: ${error.message}`);
            socket.close(1000);
        }
    }

    renderProgress() {
        const file = this.state.progress[this.state.progressIndex];
        let statusText = null;
        let statusIcon = null;
        switch (file.status) {
            case UploadStatus.QUEUED:
                statusText = "Queued...";
                statusIcon = (<i className="Queued fas fa-sync"></i>);
                break;
            case UploadStatus.UPLOADING:
                statusText = "Uploading...";
                statusIcon = (<i className="Uploading fas fa-sync"></i>);
                break;
            case UploadStatus.COMPLETED:
                statusText = "Complete";
                statusIcon = (<i className="Completed far fa-circle"></i>);
                break;
            case UploadStatus.CANCELLED:
                statusText = file.error;
                statusIcon = (<i className="Cancelled fas fa-times"></i>);
                break;
            default:
                throw new Error("FileUpload progress popup reached default switch statement");
        }
        const status = (
            <div className="Status">
                {statusIcon} {statusText} {this.state.progressIndex + 1}/{this.state.progress.length}
            </div>
        );
        const progress = Math.floor(file.progress * 100);
        return (
            <div className="FileUpload-Progress">
                <div className="Info">
                    <div className="File">{file.name}</div>
                    {status}
                </div>
                <div className="Bar">
                    <div className="Filled" style={{width: `${progress}%`}}></div>
                    <div className="Empty"></div>
                </div>
            </div>
        );
    }

    render() {
        return (
            <div
                className="FileUpload-DropZone"
                onDragOver={e => this.handleDragOver(e)}
                onDragEnter={() => this.setState({showOverlay: true})}
            >
                <CSSTransition
                    in={this.state.showOverlay}
                    timeout={500}
                    classNames="FileUpload-Overlay"
                    mountOnEnter
                    unmountOnExit
                >
                    <div
                        className="FileUpload-Overlay"
                        onDrop={e => this.handleFileDrop(e)}
                        onDragOver={e => this.handleDragOver(e)}
                        onDragEnter={() => this.setState({showOverlay: true})}
                        onDragLeave={() => this.setState({showOverlay: false})}
                    >
                        <div className="FileUpload-Overlay-Container">
                            <i className="fas fa-cloud-upload-alt"></i>
                            <div>Drag & Drop Upload</div>
                        </div>
                    </div>
                </CSSTransition>
                <FileUploadContext.Provider value={(files) => this.upload(files)}>
                    {this.props.children}
                </FileUploadContext.Provider>
                <CSSTransition
                    in={this.state.showProgress}
                    timeout={2200}
                    classNames="FileUpload-Progress"
                    mountOnEnter
                    unmountOnExit
                >
                    {() => this.renderProgress()}
                </CSSTransition>
            </div>
        );
    }
}
