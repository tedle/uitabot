// --- App.js ------------------------------------------------------------------
// Main component containing the frontend app

import "./App.scss";

import React from "react";
import * as Config from "config";
import * as Message from "utils/Message";
import * as Session from "utils/Session";
import * as DiscordOauth from "utils/DiscordOauth";
import RandomString from "utils/RandomString";
import Authenticate from "./Authenticate/Authenticate";
import Dashboard from "./Dashboard/Dashboard";
import * as Error from "./Error/Error";
import Loading from "./Loading/Loading";
import Login from "./Login/Login";
import ServerSelect from "./ServerSelect/ServerSelect";

export default class App extends React.Component {
    constructor(props) {
        super(props);

        // Stores main app state determining auth status, connection, etc
        this.state = {
            connection: WebSocket.CLOSED,
            needLogin: false,
            discordUser: null,
            discordServer: null,
            errors: Array()
        };

        // Interval callback handler for sending heartbeat packets to server
        this.heartbeatInterval = null;
    }

    componentDidMount() {
        // Initialize server event callbacks that need to be handled at the root level
        this.eventDispatcher = new Message.EventDispatcher();

        // Handler for authentication failure
        this.eventDispatcher.setMessageHandler("auth.fail", m => {
            this.setState({needLogin: true})
        });

        // Handler for authentication success
        this.eventDispatcher.setMessageHandler("auth.succeed", m => {
            Session.store({handle: m.user.session.handle, secret: m.user.session.secret});
            // Just incase we have some kind of injectable XSS nastiness
            delete m.user.session;
            this.setState({discordUser: m.user});
            // Server will close connection if it doesn't receive a packet after 90 seconds
            this.heartbeatInterval = setInterval(
                () => this.socket.send(new Message.HeartbeatMessage().str()),
                60000
            );
        });

        // Handler for server kick messages
        this.eventDispatcher.setMessageHandler("server.kick", m => {
            this.setState({discordServer: null})
        });

        // Setup the websocket after we're ready to receive and act on messages
        try {
            this.socket = new WebSocket(Config.bot_url);
            this.socket.onmessage = e => this.eventDispatcher.dispatch(Message.parse(e.data));
            this.socket.onerror = e => this.onError(e);
            this.socket.onclose = e => this.onSocketClose();
            this.socket.onopen = e => this.onSocketOpen();
            this.setState({connection: this.socket.readyState});
        }
        catch (e) {
            this.onError(e);
            this.setState({connection: WebSocket.CLOSED});
        }
    }

    componentWillUnmount() {
        this.setState({errors: Array()});
    }

    onError(message) {
        const error = {
            id: RandomString(16),
            message: message
        };
        this.setState({errors: this.state.errors.concat([error])});

        setTimeout(() => {
            this.onErrorRemove(error.id);
        }, 5000);
    }

    onErrorRemove(id) {
        // Equivilent to a this.isMounted check... kind of dirty, but reliable enough
        if (this.state.errors.length == 0) {
            return;
        }
        this.setState({errors: this.state.errors.filter(e => e.id != id)});
    }

    onSocketOpen() {
        this.setState({connection: WebSocket.OPEN});
    }

    onSocketClose() {
        this.setState({connection: WebSocket.CLOSED});
        clearInterval(this.heartbeatInterval);
    }

    componentWillUnmount() {
        this.socket.close();
        this.eventDispatcher.clearMessageHandler("auth.fail");
        this.eventDispatcher.clearMessageHandler("auth.succeed");
        this.eventDispatcher.clearMessageHandler("server.kick");
    }

    // Big, messy state machine acting as a view router
    renderView() {
        // Display the login page if authentication has failed
        if (this.state.needLogin) {
            const oauthUrl = DiscordOauth.createOauthUrl(Config.client_id, Config.client_url);
            return <Login url={oauthUrl}/>;
        }

        // Establishing connection with backend, SSL handshake, etc
        if (this.state.connection == WebSocket.CONNECTING) {
            return <Loading>Connecting</Loading>;
        }

        // Connection error displays when server closes connection
        if (this.state.connection != WebSocket.OPEN) {
            return <Error.Fatal>Connection error. <a href="/">Refresh</a>?</Error.Fatal>
        }

        // Attempt authentication with stored credentials (if they exist)
        if (this.state.discordUser === null) {
            return <Authenticate
                socket={this.socket}
                onAuthFail={() => this.setState({needLogin: true})}
            />;
        }

        // Authentication succeeded but we haven't selected a server to play music in yet
        if (this.state.discordServer === null) {
            return <ServerSelect
                socket={this.socket}
                eventDispatcher={this.eventDispatcher}
                onServerSelect={server => this.setState({discordServer: server})}
            />;
        }

        // Main view for queueing music and everything else
        return <Dashboard
            socket={this.socket}
            eventDispatcher={this.eventDispatcher}
            discordUser={this.state.discordUser}
            discordServer={this.state.discordServer}
        />;
    }

    render() {
        return (
            <Error.Context.Provider value={(error) => this.onError(error)}>
                {this.renderView()}
                <Error.List errors={this.state.errors} onRemove={id => this.onErrorRemove(id)}/>
            </Error.Context.Provider>
        );
    }
}
