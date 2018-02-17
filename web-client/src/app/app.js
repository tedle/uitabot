import React from "react";
import * as Config from "config";
import * as Message from "./message.js";
import Authenticate from "./authenticate.js";

export default class App extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            authenticated: false,
            connection: WebSocket.CLOSED
        };
        this.eventDispatcher = new Message.EventDispatcher();
        this.eventDispatcher.onAuthFail = m => console.log("Authentication failed");
    }

    componentDidMount() {
        console.log(`Connecting to ${Config.bot_url}`);
        try {
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
        if (this.state.connection == WebSocket.CONNECTING) {
            return <p>connecting</p>;
        }
        else if (this.state.connection != WebSocket.OPEN) {
            return <p>connection error</p>;
        }
        if (!this.state.authenticated) {
            return <Authenticate socket={this.socket}/>;
        }
        return <p>hello</p>;
    }
}
