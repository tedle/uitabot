// --- dashboard.js ------------------------------------------------------------
// Component for interacting with the backend bot, contains music list, etc

import React from "react";
import LivePlaylist from "./live-playlist.js";
import VoiceChannelSelect from "./voice-channel-select.js";

export default class Dashboard extends React.Component {
    constructor(props) {
        super(props);
    }

    render() {
        return (
            <div>
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
            </div>
        );
    }
}
