// --- Dashboard.js ------------------------------------------------------------
// Component for interacting with the backend bot, contains music list, etc

import "./Dashboard.scss";

import React from "react";
import FileUploadDropZone from "./FileUpload/FileUpload";
import Header from "./Header/Header";
import TabSelect from "./TabSelect/TabSelect";
import LivePlaylist from "./LivePlaylist/LivePlaylist";
import SearchBox from "./SearchBox/SearchBox";
import VoiceChannelSelect from "./VoiceChannelSelect/VoiceChannelSelect";

export default class Dashboard extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            activeTab: "playlist"
        };
    }

    render() {
        return (
            <div className="Dashboard">
                {/* Files dropped here are uploaded and queued */}
                <FileUploadDropZone
                    eventDispatcher={this.props.eventDispatcher}
                    discordServer={this.props.discordServer}
                >
                    <div className="Dashboard-Inner">
                        <div className={`Dashboard-Playlist ${this.state.activeTab=="playlist" ? "" : "hidden-xs"}`}>
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
                        </div>
                        <div className={`Dashboard-VoiceChannel ${this.state.activeTab=="voice" ? "" : "hidden-xs"}`}>
                            {/* Controls which channel the bot plays music in */}
                            <VoiceChannelSelect
                                socket={this.props.socket}
                                eventDispatcher={this.props.eventDispatcher}
                            />
                        </div>
                        <div className="Dashboard-TabSelect visible-xs">
                            <TabSelect
                                tabs={[
                                    {id: "playlist", display: "Playlist"},
                                    {id: "voice", display: "Voice Channels"}
                                ]}
                                active={this.state.activeTab}
                                onSelect={id => this.setState({activeTab: id})}
                            />
                        </div>
                        <div className="Dashboard-Header">
                            <Header
                                discordUser={this.props.discordUser}
                                discordServer={this.props.discordServer}
                            />
                        </div>
                    </div>
                </FileUploadDropZone>
            </div>
        );
    }
}
