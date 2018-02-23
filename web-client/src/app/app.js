import React from "react";
import * as Config from "config";
import * as Message from "./message.js";
import * as Session from "./session.js";
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
    }

    componentDidMount() {
        this.eventDispatcher = new Message.EventDispatcher();
        this.eventDispatcher.onAuthFail = m => this.setState({needLogin: true});
        this.eventDispatcher.onAuthSucceed = m => {
            Session.store({handle: m.session_handle, secret: m.session_secret});
            this.setState({authenticated: true});
        };
        try {
            console.log(`Connecting to ${Config.bot_url}`);
            this.socket = new WebSocket(Config.bot_url);
            this.socket.onmessage = e => this.eventDispatcher.dispatch(Message.parse(e.data));
            this.socket.onerror = e => console.log(e);
            this.socket.onclose = e => this.setState({connection: WebSocket.CLOSED});
            this.socket.onopen = e => this.setState({connection: WebSocket.OPEN});
            this.setState({connection: this.socket.readyState});
        }
        catch (e) {
            console.log(e);
            this.setState({connection: WebSocket.CLOSED});
        }
    }

    componentWillUnmount() {
        this.socket.close();
    }

    render() {
        if (this.state.needLogin) {
            return <p>need to <a href="/?code=access-code">login</a></p>;
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
