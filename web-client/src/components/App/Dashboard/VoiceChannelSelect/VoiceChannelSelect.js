// --- VoiceChannelSelect.js ---------------------------------------------------
// Component for commanding bot to join voice channels

import React from "react";
import * as Message from "utils/Message";

export default class VoiceChannelSelect extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            channels: Array(),
            activeChannelId: null
        };
    }

    componentDidMount() {
        // Once mounted, bind the event dispatchers callback for channel list queries
        this.props.eventDispatcher.setMessageHandler("channel.list.send", m => {
            this.setState({channels: m.channels});
        });
        this.props.eventDispatcher.setMessageHandler("channel.active.send", m => {
            if (m.channel !== null) {
                this.setState({activeChannelId: m.channel.id});
            } else {
                this.setState({activeChannelId: null});
            }
        });
        this.getChannelList();
    }

    componentWillUnmount() {
        this.props.eventDispatcher.clearMessageHandler("channel.list.send");
        this.props.eventDispatcher.clearMessageHandler("channel.active.send");
    }

    joinChannel(id) {
        this.props.socket.send(new Message.ChannelJoinMessage(id).str());
    }

    leaveChannel() {
        this.props.socket.send(new Message.ChannelLeaveMessage().str());
    }

    getChannelList() {
        this.props.socket.send(new Message.ChannelListGetMessage().str());
        this.props.socket.send(new Message.ChannelActiveGetMessage().str());
    }

    render() {
        // Sort the channels by position, even though discord.py doesn't generate them properly
        // At least it's consistent
        const channelList = this.state.channels
            .sort((a, b) => {
                return a.position - b.position;
            })
            .map((channel) => {
            return (
                <li key={channel.id}>
                    <button onClick={() => this.joinChannel(channel.id)}>
                        {this.state.activeChannelId == channel.id ? (
                            <span>O</span>
                        ) : (
                            <span>X</span>
                        )}
                        {channel.name}
                    </button>
                </li>
            );
        });
        return (
            <div className="VoiceChannelSelect">
                <h2>Voice Channels</h2>
                <ul>{channelList}</ul>
                {this.state.activeChannelId !== null &&
                    <button onClick={() => this.leaveChannel()}>disconnect</button>
                }
            </div>
        );
    }
}
