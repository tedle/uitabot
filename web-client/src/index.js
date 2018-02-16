import React from "react";
import ReactDOM from "react-dom";
import * as Config from "config";

class App extends React.Component {
    componentDidMount() {
        console.log(`Connecting to ${Config.bot_url}`);
        try {
            this.socket = new WebSocket(Config.bot_url);
            this.socket.onmessage = e => console.log(e);
            this.socket.onerror = e => console.log(e);
            this.socket.onclose = e => console.log(e);
            this.socket.onopen = e => this.socket.send('{"header":"auth_session","user":"me","session":"12345"}');
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

ReactDOM.render(<App/>, document.getElementById("root"));
