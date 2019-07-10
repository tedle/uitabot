// --- FileUpload.js -----------------------------------------------------------
// Component for drag and drop file uploads via websocket

import "./FileUpload.scss";

import React from "react";
import {CSSTransition} from "react-transition-group";
import * as Config from "config";
import * as Message from "utils/Message";
import * as Session from "utils/Session";
import * as Error from "components/App/Error/Error";
import ContextAsProp from "utils/ContextAsProp";

var UploadStatus = {
    QUEUED: 1,
    UPLOADING: 2,
    COMPLETED: 3,
    CANCELLED: 4
};
Object.freeze(UploadStatus);

// Allows nested components to upload files programmatically (upload buttons, etc)
export const FileUploadContext = React.createContext(() => {});

class DropZone extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            progress: Array(),
            progressIndex: 0,
            showProgress: false
        };
        this._isMounted = false;
        this._isUploading = false;
        this._cancelUploadFlag = false;
        this.uploadQueue = Array();
    }

    componentDidMount() {
        this._isMounted = true;
    }

    componentWillUnmount() {
        this._isMounted = false;
    }

    cancelUploads() {
        this._cancelUploadFlag = true;
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
        // Stream the file data in chunks
        //
        // Ideally this number scales depending on the user's ping and bandwidth to get the best
        // available throughput, but that is a lot of added effort for a small feature in a small
        // project.
        const chunk_size = 1024 * 512;
        let start = 0;
        let end = 0;
        while (end < file.size) {
            // Wait for the server response
            await this.fileReady(dispatcher);
            start = end;
            end = Math.min(end + chunk_size, file.size);
            socket.send(file.slice(start, end));
            if (!this._isMounted || this._cancelUploadFlag) {
                throw "Cancelled";
            }
            progressCallback(file.size - end);
        }
        // Wait for the server response
        await this.fileComplete(dispatcher, socket);
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
            setTimeout(() => reject("Server timed out or disconnected"), 30000);
        });
    }

    fileComplete(dispatcher, socket) {
        // Create an awaitable event that triggers after a server response
        return new Promise((resolve, reject) => {
            let complete = false;
            dispatcher.setMessageHandler("file.upload.complete", m => {
                complete = true;
                resolve();
            });
            dispatcher.setMessageHandler("error.file.invalid", m => {
                complete = true;
                reject(m.error);
            });
            dispatcher.setMessageHandler("error.queue.full", m => {
                complete = true;
                reject("Queue is full");
            });
            let oldBufferedAmount = socket.bufferedAmount;
            let bufferInterval = setInterval(() => {
                if (oldBufferedAmount == socket.bufferedAmount || complete) {
                    complete = true;
                    clearInterval(bufferInterval);
                    reject("Server timed out or disconnected");
                }
                oldBufferedAmount = socket.bufferedAmount;
            }, 5000);
            let cancelInterval = setInterval(() => {
                if (this._cancelUploadFlag || complete) {
                    complete = true;
                    clearInterval(cancelInterval);
                    reject("Cancelled");
                }
            }, 200);
        });
    }

    upload(files) {
        if (files.length == 0) {
            return;
        }
        // Append given files to the upload queue for the running task to handle
        this.uploadQueue = this.uploadQueue.concat(files.map(file => {
            return {
                name: file.name,
                size: file.size,
                progress: 0.0,
                status: UploadStatus.QUEUED,
                blob: file,
                error: ""
            };
        }));
        if (!this._isUploading) {
            this._spawnUploadTask();
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
                    <button className="CancelUploads" onClick={() => this.cancelUploads()}>
                        <i className="fas fa-times"></i>
                    </button>
                </div>
                <div className="Bar">
                    <div className="Filled" style={{width: `${progress}%`}}></div>
                    <div className="Empty"></div>
                </div>
            </div>
        );
    }

    _spawnUploadTask() {
        // Create a new authenticated socket to do the file uploads from asynchronously without
        // jamming up the send buffer queue
        let eventDispatcher = new Message.EventDispatcher();
        let socket = new WebSocket(Config.bot_url);
        try {
            this._isUploading = true;
            // Load up the stored credentials that absolutely most likely exist
            let session = Session.load();
            if (session === null) {
                throw new Error("No session cookie");
            }
            // Initialize socket callbacks
            socket.onmessage = e => eventDispatcher.dispatch(Message.parse(e.data));
            socket.onerror = e => this.props.onError(e);
            socket.onopen = e => {
                socket.send(new Message.AuthSessionMessage(session.handle, session.secret).str());
            };
            // After authentication, join the selected server and upload the files
            eventDispatcher.setMessageHandler("auth.succeed", async (m) => {
                await this._uploadTask(socket, eventDispatcher);
            });
            // There is a very rare chance that the server side credentials have expired and failed to renew
            eventDispatcher.setMessageHandler("auth.fail", m => {
                this._isUploading = false;
                this.props.onError("File upload authentication failed. Try refreshing.");
                socket.close(1000);
            });
        } catch (error) {
            this._isUploading = false;
            this.props.onError(`File upload error: ${error.message}`);
            socket.close(1000);
        }
    }

    async _uploadTask(socket, dispatcher) {
        try {
            // Select the server to upload files to
            socket.send(new Message.ServerJoinMessage(this.props.discordServer.id).str());
            let index = -1;
            // Recheck the queue after each upload in case new files are added
            while ((index = this.uploadQueue.findIndex(f => f.status == UploadStatus.QUEUED)) != -1) {
                try {
                    if (socket.readyState != WebSocket.OPEN) {
                        throw new Error("Server disconnected");
                    }
                    if (this._cancelUploadFlag) {
                        throw new Error("Cancelled");
                    }

                    this.setState({
                        progress: this.uploadQueue,
                        progressIndex: index,
                        showProgress: true
                    });

                    const file = this.uploadQueue[index];
                    await this.fileSend(file.blob, socket, dispatcher, (buffered) => {
                        this.uploadQueue[index].status = UploadStatus.UPLOADING;
                        this.uploadQueue[index].progress = (file.size - buffered) / file.size;
                        this.setState({progress: this.uploadQueue, showProgress: true});
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
                    this.uploadQueue[index].status = UploadStatus.COMPLETED;
                } catch (error) {
                    this.uploadQueue[index].status = UploadStatus.CANCELLED;
                    this.uploadQueue[index].error = error;
                } finally {
                    this.uploadQueue[index].progress = 1.0;
                    this.setState({progress: this.uploadQueue, showProgress: true});
                }
            }
        } finally {
            // Make sure that _isUploading resets in the same synchronous control block as the
            // while loop exits, so the component knows to spawn new tasks for later files
            this._isUploading = false;
            this.uploadQueue = Array();
            this._cancelUploadFlag = false;
            this.setState({showProgress: false});
            socket.close(1000);
        }
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

export default ContextAsProp(DropZone, Error.Context, "onError");
