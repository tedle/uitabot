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
        // React deprecated isMounted() because they think you should implement a janky, only
        // sometimes functional, canellable promise wrapper around every async function call you
        // make so that running promises can be cleaned up on unmount, sometimes, if you're lucky
        // and built them in just the right way. Instead we will just track that state ourselves.
        this._isMounted = false;
    }

    componentDidMount() {
        this._isMounted = true;

        // Handler for URL errors
        this.props.eventDispatcher.setMessageHandler("error.url.invalid", m => {
            alert("ERROR: We sent a bad URL");
        });
        this.props.eventDispatcher.setMessageHandler("error.queue.full", m => {
            alert("ERROR: The queue is full");
        });
    }

    componentWillUnmount() {
        this._isMounted = false;
        this.cancelRunningQueries();
        this.props.eventDispatcher.clearMessageHandler("error.url.invalid");
    }

    cancelRunningQueries() {
        if (this.searchTimeout != null) {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = null;
        }
    }

    focus() {
        this.searchInput.focus();
    }

    async search(query) {
        try {
            const results = await Youtube.search(query);
            if (this._isMounted && this.state.searchBox == query) {
                this.setState({searchResults: results});
            }
            const detailedResults = await Youtube.searchDetails(results);
            if (this._isMounted && this.state.searchBox == query) {
                this.setState({searchResults: detailedResults});
            }
        } catch (error) {
            console.log(error);
        }
    }

    isQuery(query) {
        return (query.length > 0 && !this.isUrl(query));
    }

    isUrl(url) {
        return /^http(s)?:\/\//.test(url);
    }

    setSearchBox(query) {
        // Sync input box value with component state
        this.setState({searchBox: query});
        // Cancel any currently running search queries
        this.cancelRunningQueries();
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
                this.cancelRunningQueries();
                this.search(input);
            }
            // URLs get sent to the backend
            else if (this.isUrl(input)) {
                this.submitUrl(this.state.searchBox);
            }
        }
    }

    handleSearchResultClick(url) {
        this.setSearchBox("");
        this.submitUrl(url);
        this.focus();
    }

    render() {
        // Map the search results JSON object into component nodes
        let searchResults = [];
        if (this.state.searchResults != null) {
            searchResults = this.state.searchResults
                .map(result => {
                    return (
                        <li key={result.id}>
                            <img src={result.thumbnail}/>
                            <button onClick={() => this.handleSearchResultClick(result.url)}>
                                {result.display()}
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
