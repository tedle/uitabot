// --- Authenticate.js ---------------------------------------------------------
// Component for doing backend authentication

import React from "react";
import * as QueryString from "query-string";
import * as Message from "utils/Message";
import * as Session from "utils/Session";
import * as DiscordApi from "utils/DiscordApi";
import Loading from "components/App/Loading/Loading";

export default class Authenticate extends React.Component {
    constructor(props) {
        super(props);
    }

    componentDidMount() {
        // Main authentication protocol
        this.auth(this.props.socket);
    }

    auth(socket) {
        try {
            // Start by checking if we've redirected from a Discord OAuth requested
            const query = QueryString.parse(location.search);
            if ("code" in query && "state" in query) {
                // When using OAuth we pass a state parameter along with the request to prevent CSRF
                // and stuff. This is the part where we make sure Discord sent back what we sent it
                if (!DiscordApi.verifyState(query.state)) {
                    throw new Error("No state parameter with auth code");
                }

                // Send the auth code to the server so it can turn it into an auth token
                socket.send(new Message.AuthCodeMessage(query.code).str());

                // Strip query string from URL
                window.history.replaceState(null, null, window.location.pathname);
                return;
            }

            // Since we're not coming back from Discord's site, let's try and load old credentials
            let session = Session.load();
            if (session === null) {
                throw new Error("No session cookie");
            }
            socket.send(new Message.AuthSessionMessage(session.handle, session.secret).str());
        } catch (e) {
            // If any of these steps failed we can trigger the auth failure immediately.
            // Otherwise we have to wait for the server to respond and tell us how we did, which
            // is handled by the main App component.
            this.props.onAuthFail();
            socket.close(1000, e.message);
            return;
        }
    }

    render() {
        return <Loading>Authenticating</Loading>;
    }
}
