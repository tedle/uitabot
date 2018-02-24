import React from "react";
import * as QueryString from "query-string";
import * as Message from "./message.js";
import * as Session from "./session.js";
import * as DiscordOauth from "./discord-oauth.js";

export default class Authenticate extends React.Component {
    constructor(props) {
        super(props);
    }

    componentDidMount() {
        this.auth(this.props.socket);
    }

    auth(socket) {
        try {
            const query = QueryString.parse(location.search);
            if ("code" in query && "state" in query) {
                if (!DiscordOauth.verifyState(query.state)) {
                    throw new Error("No state parameter with auth code");
                }
                socket.send(new Message.AuthCodeMessage(query.code).str());
                // Strip query string from URL
                window.history.replaceState(null, null, window.location.pathname);
                return;
            }
            let session = Session.load();
            if (session === null) {
                throw new Error("No session cookie");
            }
            socket.send(new Message.AuthSessionMessage(session.handle, session.secret).str());
        } catch (e) {
            this.props.onAuthFail();
            socket.close(1000, e.message);
            return;
        }
    }

    render() {
        return <p>authing</p>;
    }
}
