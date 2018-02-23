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
        this.props.eventDispatcher.onServerListSend = m => this.setState({servers: m.servers});
        this.getServerList();
    }

    getServerList(socket) {
        this.props.socket.send(new Message.ServerListGetMessage().str());
    }

    joinServer(id) {
        this.props.socket.send(new Message.ServerJoinMessage(id).str());
        this.props.onServerSelect(id);
    }

    render() {
        const serverList = this.state.servers.map((server) => {
            return (
                <li key={server.id}>
                    <button onClick={() => this.joinServer(server.id)}>{server.name}</button>
                </li>
            );
        });
        return (
            <div>
                <p>future server game</p>
                <ul>{serverList}</ul>
            </div>
        );
    }
}
