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
        this.getServerList(this.props.socket);
    }

    getServerList(socket) {
        socket.send(new Message.ServerListGetMessage().str());
    }

    render() {
        const serverList = this.state.servers.map((server) => {
            return <li key={server.id}>{server.name}</li>;
        });
        return (
            <div>
                <p>future server game</p>
                <ul>{serverList}</ul>
            </div>
        );
    }
}
