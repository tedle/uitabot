import React from "react";
import * as QueryString from "query-string";
import * as Message from "./message.js";

export default class Authenticate extends React.Component {
    constructor(props) {
        super(props);
    }

    componentDidMount() {
        this.auth(this.props.socket);
    }

    auth(socket) {
        const query = QueryString.parse(location.search);
        if ('code' in query) {
            socket.send(new Message.AuthTokenMessage(code).str());
        }
        socket.send(new Message.AuthSessionMessage("12345", "me").str());
    }

    render() {
        return <p>authing</p>;
    }
}
