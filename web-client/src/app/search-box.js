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
        // setTimeout callback is stored so that it can be cancelled when overwritten
        this.searchTimeout = null;
    }

    focus() {
        this.searchInput.focus();
    }

    async search(query) {
        const response = await Youtube.search(query);
        if (!response.ok) {
            this.setState({searchResults: null});
            console.log(`Youtube API failed with code ${response.status}`);
            return;
        }
        // If the query box has already changed don't bother storing the results
        if (this.isQuery(this.state.searchBox)) {
            this.setState({searchResults: await response.json()});
        }
    }

    isQuery(query) {
        return (query.length > 0 && !this.isUrl(query));
    }

    isUrl(url) {
        return RegExp("^http(s)?:\\/\\/").test(url);
    }

    setSearchBox(query) {
        // Sync input box value with component state
        this.setState({searchBox: query});
        // Cancel any currently running search queries
        if (this.searchTimeout != null) {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = null;
        }
        // Do a search if the box isn't empty and isn't a URL
        if (this.isQuery(query)) {
            this.searchTimeout = setTimeout(() => this.search(query), 500);
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
            const input = this.state.searchBox;
            // Search queries get sent to Youtube
            if (this.isQuery(input)) {
                if (this.searchTimeout != null) {
                    clearTimeout(this.searchTimeout);
                    this.searchTimeout = null;
                }
                this.search(input);
            }
            // URLs get sent to the backend
            else if (this.isUrl(input)) {
                this.submitUrl(this.state.searchBox);
            }
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
