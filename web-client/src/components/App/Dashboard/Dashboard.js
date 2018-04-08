// --- Dashboard.js ------------------------------------------------------------
// Component for interacting with the backend bot, contains music list, etc

import React from "react";
import FileUploadDropZone from "./FileUpload/FileUpload";
import LivePlaylist from "./LivePlaylist/LivePlaylist";
import SearchBox from "./SearchBox/SearchBox";
import VoiceChannelSelect from "./VoiceChannelSelect/VoiceChannelSelect";

export default class Dashboard extends React.Component {
    constructor(props) {
        super(props);
    }

    render() {
        return (
            <div>
                {/* Searches for and queues audio */}
                <SearchBox
                    socket={this.props.socket}
                    eventDispatcher={this.props.eventDispatcher}
                />
                {/* Shows current music queue, handles song searches, etc */}
                <LivePlaylist
                    socket={this.props.socket}
                    eventDispatcher={this.props.eventDispatcher}
                />
                {/* Controls which channel the bot plays music in */}
                <VoiceChannelSelect
                    socket={this.props.socket}
                    eventDispatcher={this.props.eventDispatcher}
                />
                {/* Files dropped here are uploaded and queued */}
                <FileUploadDropZone
                    socket={this.props.socket}
                    eventDispatcher={this.props.eventDispatcher}
                    discordServer={this.props.discordServer}
                />
            </div>
        );
    }
}
