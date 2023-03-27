// --- ServerSelect.js ---------------------------------------------------------
// Component for selecting the server to play music in

import "./ServerSelect.scss";

import React from "react";
import PropTypes from "prop-types";
import * as Message from "utils/Message";
import * as Session from "utils/Session";

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
            this.setState({servers: m.servers});
        });
        this.getServerList();
    }

    componentWillUnmount() {
        this.props.eventDispatcher.clearMessageHandler("server.list.send");
    }

    getServerList() {
        this.props.socket.send(new Message.ServerListGetMessage().str());
    }

    joinServer(server) {
        this.props.socket.send(new Message.ServerJoinMessage(server.id).str());
        this.props.onServerSelect(server);
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
                        <button onClick={() => this.joinServer(server)}>
                            {server.icon === null ? (
                                <i className="NullLogo fab fa-discord"></i>
                            ) : (
                                <img src={server.icon}/>
                            )}
                            <span>{server.name}</span>
                            <i className="EndIcon fas fa-angle-right"></i>
                        </button>
                    </li>
                );
            });

        // Display the list and an amazing gaming culture reference. It is very funny
        return (
            <div className="ServerSelect">
                <h1>Future Server Game</h1>
                {serverList.length > 0 ? (
                    <ul>{serverList}</ul>
                ) : (
                    <div className="NoServers">
                        <i className="far fa-times-circle"></i> No Servers
                    </div>
                )}
                <div className="Options">
                    <button onClick={Session.logout}>
                        <i className="fas fa-sign-out-alt"></i> Logout
                    </button>
                </div>
            </div>
        );
    }
}

ServerSelect.propTypes = {
    eventDispatcher: PropTypes.instanceOf(Message.EventDispatcher).isRequired,
    socket: PropTypes.instanceOf(WebSocket).isRequired,
    onServerSelect: PropTypes.func.isRequired
};
