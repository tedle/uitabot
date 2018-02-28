// --- server-select.js --------------------------------------------------------
// Component for selecting the server to play music in

import React from "react";
import * as Message from "./message.js";

export default class ServerSelect extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            servers: Array()
        };
    }

    componentDidMount() {
        // Once mounted, bind the event dispatchers callback for server list queries
        this.props.eventDispatcher.setMessageHandler("server.list.send", m => {
            this.setState({servers: m.servers})
        });
        this.getServerList();
    }

    componentWillUnmount() {
        this.props.eventDispatcher.clearMessageHandler("server.list.send");
    }

    getServerList(socket) {
        this.props.socket.send(new Message.ServerListGetMessage().str());
    }

    joinServer(id) {
        this.props.socket.send(new Message.ServerJoinMessage(id).str());
        this.props.onServerSelect(id);
    }

    render() {
        // Sort the servers alphabetically and then generate a list element with a join button
        const serverList = this.state.servers
            .sort((a, b) => {
                return a.name.localeCompare(b.name);
            })
            .map((server) => {
            return (
                <li key={server.id}>
                    <button onClick={() => this.joinServer(server.id)}>{server.name}</button>
                </li>
            );
        });

        // Display the list and an amazing gaming culture reference. It is very funny
        return (
            <div>
                <p>future server game</p>
                <ul>{serverList}</ul>
            </div>
        );
    }
}
