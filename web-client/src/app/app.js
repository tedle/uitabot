import React from "react";
import * as Config from "config";
import authenticate from "./authenticate.js";

export default class App extends React.Component {
    componentDidMount() {
        console.log(`Connecting to ${Config.bot_url}`);
        try {
            this.socket = new WebSocket(Config.bot_url);
            this.socket.onmessage = e => dispatchMessage(e);
            this.socket.onerror = e => console.log(e);
            this.socket.onclose = e => console.log(e);
            this.socket.onopen = e => authenticate(this.socket);
        }
        catch (e) {
            console.log(e);
        }
    }

    componentWillUnmount() {
        this.socket.close();
    }

    render() {
        return <p>hello</p>;
    }
}

function dispatchMessage(message) {
    console.log(message);
}
