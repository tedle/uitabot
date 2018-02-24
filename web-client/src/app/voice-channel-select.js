import React from "react";
import * as Message from "./message.js";

export default class VoiceChannelSelect extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            channels: Array()
        };
    }

    componentDidMount() {
        this.props.eventDispatcher.onChannelListSend = m => this.setState({channels: m.channels});
        this.getChannelList();
    }

    getChannelList(socket) {
        this.props.socket.send(new Message.ChannelListGetMessage().str());
    }

    render() {
        const channelList = this.state.channels
            .sort((a, b) => {
                return a.position - b.position;
            })
            .map((channel) => {
            return (
                <li key={channel.id}>
                    <button onClick={() => this.joinServer(channel.id)}>{channel.name}</button>
                </li>
            );
        });
        return (
            <div>
                <p>voice channel select</p>
                <ul>{channelList}</ul>
            </div>
        );
    }
}
