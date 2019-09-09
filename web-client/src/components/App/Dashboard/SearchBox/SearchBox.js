// --- SearchBox.js ------------------------------------------------------------
// Component for searching and queueing audio

import "./SearchBox.scss";

import React from "react";
import PropTypes from "prop-types";
import {CSSTransition} from "react-transition-group";
import TouchButton from "components/TouchButton/TouchButton";
import * as Message from "utils/Message";
import * as Youtube from "utils/YoutubeApi";
import {FileUploadContext} from "components/App/Dashboard/FileUpload/FileUpload";
import * as Errors from "components/App/Errors/Errors";
import ContextAsProp from "utils/ContextAsProp";

class SearchBox extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            searchBox: "",
            searchResults: null,
            // Separate state so results may be referenced during transitions and deleted later
            searchShowResults: false
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
            this.props.onError("Invalid URL requested");
        });
        this.props.eventDispatcher.setMessageHandler("error.queue.full", m => {
            this.props.onError("Playback queue is full");
        });
    }

    componentWillUnmount() {
        this._isMounted = false;
        this.cancelRunningQueries();
        this.setState({searchShowResults: false});
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
            // Display the results popup immediately for a more responsive feel
            this.setState({
                searchResults: null,
                searchShowResults: true
            });
            // A YouTube search only provides cursory info, things like duration are not included
            const results = await Youtube.search(query);
            if (this._isMounted && this.state.searchBox == query) {
                this.setState({searchResults: results});
            }
            // So after updating with the basic info, we make a new quest for detailed results
            const detailedResults = await Youtube.searchDetails(results);
            if (this._isMounted && this.state.searchBox == query) {
                this.setState({searchResults: detailedResults});
            }
        } catch (error) {
            this.props.onError(error);
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
            this.setState({searchShowResults: false});
        }
    }

    submitInput() {
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
            this.submitInput();
        }
    }

    handleSearchResultClick(url, tapped) {
        this.setSearchBox("");
        this.submitUrl(url);
        // Don't auto-refocus when tapped
        // This forces the on-screen keyboard for mobile devices to popup and it can be annoying
        if (!tapped) {
            this.focus();
        }
    }

    render() {
        // Map the search results JSON object into component nodes
        let searchResults = [];
        if (this.state.searchResults != null) {
            searchResults = this.state.searchResults
                .map(result => {
                    return (
                        <li key={result.id}>
                            <TouchButton
                                onClick={e => this.handleSearchResultClick(result.url, e.wasTapped)}
                            >
                                <img className="Thumbnail" src={result.thumbnail}/>
                                <div className="Description">
                                    <div className="Title">{result.title}</div>
                                    <div className="Duration">{result.displayDuration()}</div>
                                </div>
                            </TouchButton>
                        </li>
                    );
                });
        }
        // Build the final component
        return (
            <div className="SearchBox">
                <div className="SearchBox-Input">
                    <input
                        ref={(e) => this.searchInput = e}
                        type="text"
                        autoComplete="off"
                        placeholder="Search / URL"
                        onChange={e => this.handleChange(e)}
                        onKeyDown={e => this.handleKeyDown(e)}
                        value={this.state.searchBox}
                    />
                    <button onClick={() => this.submitInput()}>
                        <i className="fas fa-search"></i>
                    </button>
                    <label htmlFor="SearchBox-Upload">
                        <i className="fas fa-upload"></i>
                    </label>
                    <FileUploadContext.Consumer>
                        {upload => (
                            <input
                                id="SearchBox-Upload"
                                type="file"
                                accept="audio/*,video/*"
                                multiple
                                onChange={(e) => upload(Array.from(e.target.files))}
                            />
                        )}
                    </FileUploadContext.Consumer>
                </div>
                <CSSTransition
                    in={this.state.searchShowResults}
                    timeout={300}
                    classNames="SearchBox-Results"
                    mountOnEnter
                    unmountOnExit
                >
                    <div className="SearchBox-Results">
                        <div className="Overlay">
                            {searchResults.length > 0 ? (
                                <ul>
                                    {searchResults}
                                </ul>
                            ) : (
                                this.state.searchResults === null ? (
                                    <div className="Loading">
                                        <i className="fas fa-spinner fa-spin"></i>
                                    </div>
                                ) : (
                                    <div className="NoResults">
                                        <i className="far fa-times-circle"></i>No results found
                                    </div>
                                )
                            )}
                        </div>
                    </div>
                </CSSTransition>
            </div>
        );
    }
}

export default ContextAsProp(SearchBox, Errors.Context, "onError");

SearchBox.propTypes = {
    eventDispatcher: PropTypes.instanceOf(Message.EventDispatcher).isRequired,
    socket: PropTypes.instanceOf(WebSocket).isRequired,
    onError: PropTypes.func.isRequired
};
