// --- searchbox.js ------------------------------------------------------------
// Component for searching and queueing audio

import React from "react";
import * as Message from "./message.js";
import * as Youtube from "./youtube-api.js";

export default class SearchBox extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            searchBox: "",
            searchResults: null
        };
    }

    focus() {
        this.searchInput.focus();
    }

    setSearchBox(query) {
        // Sync input box value with component state
        this.setState({searchBox: query});
        // Do a search if the box isn't empty and isn't a URL
        if (query.length > 0 && !RegExp("^http(s)?:\\/\\/").test(query)) {
            Youtube.search(query)
                .then((response) => {
                    if (response.ok) {
                        return response.json();
                    }
                    throw new Error(`Youtube API failed with code ${response.status}`);
                })
                .then((data) => {
                    this.setState({searchResults: data});
                })
                .catch((error) => {
                    this.setState({searchResults: null});
                    console.log(error.message);
                });
        }
        else {
            this.setState({searchResults: null});
        }
    }

    submitUrl(url) {
        this.props.socket.send(new Message.PlayURLMessage(url).str());
        this.setState({searchBox: ""});
    }

    handleChange(event) {
        this.setSearchBox(event.target.value);
    }

    handleKeyDown(event) {
        // Submit search query to backend
        if (event.keyCode == 13) { // Enter
            this.submitUrl(this.state.searchBox);
        }
    }

    handleSearchResultClick(youtube_id) {
        this.setSearchBox("");
        this.submitUrl(Youtube.urlFromId(youtube_id));
        this.focus();
    }

    render() {
        // Map the search results JSON object into component nodes
        let searchResults = [];
        if (this.state.searchResults != null) {
            searchResults = this.state.searchResults.items
                .map((result) => {
                    return (
                        <li key={result.etag}>
                            <img src={result.snippet.thumbnails.default.url}/>
                            <button onClick={() => this.handleSearchResultClick(result.id.videoId)}>
                                {result.snippet.title}
                            </button>
                        </li>
                    );
            });
        }
        // Build the final component
        return (
            <div>
                <p>music goes here</p>
                <input
                    ref={(e) => this.searchInput = e}
                    type="text"
                    autoComplete="off"
                    placeholder="Search"
                    onChange={e => this.handleChange(e)}
                    onKeyDown={e => this.handleKeyDown(e)}
                    value={this.state.searchBox}
                />
                <ul>
                    {searchResults}
                </ul>
            </div>
        );
    }
}
