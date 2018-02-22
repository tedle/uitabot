import React from "react";
import * as Message from "./message.js";

export default class LivePlaylist extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            searchBox: ""
        };
    }

    handleChange(event) {
        this.setState({searchBox: event.target.value});
    }

    handleKeyDown(event) {
        if (event.keyCode == 13) { // Enter
            let file_url = this.state.searchBox;
            this.props.socket.send(new Message.PlayURLMessage(file_url).str());
            this.setState({searchBox: ""});
        }
    }

    render() {
        return (
            <div>
                <p>music goes here</p>
                <input
                    type="text"
                    autoComplete="off"
                    placeholder="Sound file URL"
                    onChange={e => this.handleChange(e)}
                    onKeyDown={e => this.handleKeyDown(e)}
                    value={this.state.searchBox}
                />
            </div>
        );
    }
}
