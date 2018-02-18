import React from "react";
import * as QueryString from "query-string";
import * as Message from "./message.js";
import * as Session from "./session.js";

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
            socket.send(new Message.AuthCodeMessage(query.code).str());
            // Strip query string from URL
            window.history.replaceState(null, null, window.location.pathname);
            return;
        }
        let session = Session.load();
        if (session === null) {
            this.props.onAuthFail();
            socket.close(1000, "No session cookie");
            return;
        }
        socket.send(new Message.AuthSessionMessage(session.handle, session.secret).str());
    }

    render() {
        return <p>authing</p>;
    }
}
