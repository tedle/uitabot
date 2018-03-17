// --- live-playlist.js --------------------------------------------------------
// Component for viewing queued music

import React from "react";
import * as Message from "./message.js";

export default class LivePlaylist extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            queue: Array()
        };
    }

    componentDidMount() {
        // Once mounted, bind the event dispatchers callback for play queue queries
        this.props.eventDispatcher.setMessageHandler("play.queue.send", m => {
            this.setState({queue: m.queue})
        });
        // Request the initial queue state
        this.props.socket.send(new Message.PlayQueueGetMessage().str());
    }

    componentWillUnmount() {
        this.props.eventDispatcher.clearMessageHandler("play.queue.send");
    }

    render() {
        const queue = this.state.queue
            .map((track) => {
            return (
                <li key={track.id}>
                    <a href={track.url}>{track.title}</a>
                </li>
            );
        });
        return (
            <div>
                <p>music queue</p>
                <ul>{queue}</ul>
            </div>
        );
    }
}
