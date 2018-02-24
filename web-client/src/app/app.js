import React from "react";
import * as Config from "config";
import * as Message from "./message.js";
import * as Session from "./session.js";
import * as DiscordOauth from "./discord-oauth.js";
import Authenticate from "./authenticate.js";
import Dashboard from "./dashboard.js";
import ServerSelect from "./server-select.js";

export default class App extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            authenticated: false,
            connection: WebSocket.CLOSED,
            needLogin: false,
            discordServer: null
        };
        this.heartbeatInterval = null;
    }

    componentDidMount() {
        this.eventDispatcher = new Message.EventDispatcher();
        this.eventDispatcher.onAuthFail = m => this.setState({needLogin: true});
        this.eventDispatcher.onAuthSucceed = m => {
            Session.store({handle: m.session_handle, secret: m.session_secret});
            this.setState({authenticated: true});
            this.heartbeatInterval = setInterval(
                () => this.socket.send(new Message.HeartbeatMessage().str()),
                60000
            );
        };
        try {
            console.log(`Connecting to ${Config.bot_url}`);
            this.socket = new WebSocket(Config.bot_url);
            this.socket.onmessage = e => this.eventDispatcher.dispatch(Message.parse(e.data));
            this.socket.onerror = e => console.log(e);
            this.socket.onclose = e => this.onSocketClose();
            this.socket.onopen = e => this.onSocketOpen();
            this.setState({connection: this.socket.readyState});
        }
        catch (e) {
            console.log(e);
            this.setState({connection: WebSocket.CLOSED});
        }
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
    }

    render() {
        if (this.state.needLogin) {
            const oauthUrl = DiscordOauth.createOauthUrl(Config.client_id, Config.client_url);
            return <p>need to <a href={oauthUrl}>login</a></p>;
        }
        if (this.state.connection == WebSocket.CONNECTING) {
            return <p>connecting</p>;
        }
        if (this.state.connection != WebSocket.OPEN) {
            return <p>connection error</p>;
        }
        if (!this.state.authenticated) {
            return <Authenticate
                socket={this.socket}
                onAuthFail={() => this.setState({needLogin: true})}
            />;
        }
        if (this.state.discordServer === null) {
            return <ServerSelect
                socket={this.socket}
                eventDispatcher={this.eventDispatcher}
                onServerSelect={(id) => this.setState({discordServer: id})}
            />;
        }
        return <Dashboard
            socket={this.socket}
            eventDispatcher={this.eventDispatcher}
        />;
    }
}
