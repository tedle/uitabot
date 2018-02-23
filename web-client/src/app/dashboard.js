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
                <LivePlaylist
                    socket={this.props.socket}
                    eventDispatcher={this.props.eventDispatcher}
                />
                <VoiceChannelSelect
                    socket={this.props.socket}
                    eventDispatcher={this.props.eventDispatcher}
                />
            </div>
        );
    }
}
