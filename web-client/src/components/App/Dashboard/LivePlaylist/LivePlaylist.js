// --- LivePlaylist.js ---------------------------------------------------------
// Component for viewing queued music

import "./LivePlaylist.scss";

import React from "react";
import PropTypes from "prop-types";
import {CSSTransition, TransitionGroup} from "react-transition-group";
import {SortableContainer, SortableElement} from "react-sortable-hoc";
import * as Message from "utils/Message";
import TimestampFormat from "utils/TimestampFormat";

export default class LivePlaylist extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            queue: Array(),
            playCurrentTime: 0
        };

        this.isPlaying = false;
        this.playStartTime = 0;
        this.playUpdateTask = null;
        // Render updates while dragging break react-sortable-hoc and playUpdateTask causes render
        // updates at frequent intervals
        this.skipPlayUpdateTask = false;
    }

    componentDidMount() {
        // Once mounted, bind the event dispatchers callback for play queue queries
        this.props.eventDispatcher.setMessageHandler("play.queue.send", m => {
            this.handleQueueChange(m.queue);
        });
        this.props.eventDispatcher.setMessageHandler("play.status.send", m => {
            switch (m.status) {
                case Message.PlayStatusSendMessage.PLAYING:
                    this.startPlayProgress();
                    break;
                case Message.PlayStatusSendMessage.PAUSED:
                    this.pausePlayProgress();
                    break;
                default:
                    throw new Error("play.status.send enum had unexpected value");
            }
        });
        // Request the initial queue state
        this.props.socket.send(new Message.PlayQueueGetMessage().str());
        this.props.socket.send(new Message.PlayStatusGetMessage().str());
    }

    componentWillUnmount() {
        this.props.eventDispatcher.clearMessageHandler("play.queue.send");
        this.props.eventDispatcher.clearMessageHandler("play.status.send");

        this.setState({queue: Array()});

        this.pausePlayProgress();
    }

    handleQueueChange(newQueue) {
        this.setState({queue: newQueue});
        this.resetPlayProgress();
    }

    handleSortStart() {
        this.skipPlayUpdateTask = true;
    }

    handleSortEnd({oldIndex, newIndex}) {
        this.skipPlayUpdateTask = false;
        this.queueMove(oldIndex, newIndex);
    }

    queueMove(oldIndex, newIndex) {
        const track = this.state.queue[oldIndex];
        // Update server
        this.props.socket.send(new Message.PlayQueueMoveMessage(track.id, newIndex).str());
        // Predictively update client
        const queue = [...this.state.queue].filter(t => t.id != track.id);
        queue.splice(newIndex, 0, track);
        this.setState({
            queue: queue
        });
    }

    queueRemove(trackId) {
        this.props.socket.send(new Message.PlayQueueRemoveMessage(trackId).str());
    }

    startPlayProgress() {
        this.pausePlayProgress();

        this.playStartTime = performance.now();
        this.setState({playCurrentTime: this.playStartTime});

        // Use recursive timeouts instead of an interval to have the timer based relative to a
        // ground truth starting point, this keeps the update calls in sync with visually distinct
        // state changes and also minimizes the amount of updates that need to be made.
        const update = () => {
            const timeOffset = this.playStartTime % 1000;
            const timeUntilNext = 1000 - (performance.now() % 1000) + timeOffset;
            this.playUpdateTask = setTimeout(update, timeUntilNext);

            if (this.skipPlayUpdateTask) {
                return;
            }

            this.setState({playCurrentTime: performance.now()});
        };
        update();

        this.isPlaying = true;
    }

    pausePlayProgress() {
        if (this.playUpdateTask != null) {
            clearInterval(this.playUpdateTask);
        }

        this.isPlaying = false;
    }

    resetPlayProgress() {
        this.playStartTime = performance.now();
        this.setState({playCurrentTime: this.playStartTime});
    }

    render() {
        return (
            <div className="LivePlaylist">
                <Playlist
                    tracks={this.state.queue}
                    playStartTime={this.playStartTime}
                    playCurrentTime={this.state.playCurrentTime}
                    onTrackRemove={(id) => this.queueRemove(id)}
                    shouldCancelStart={(e) => e.target.classList.contains("DragCancel")}
                    onSortStart={() => this.handleSortStart()}
                    onSortEnd={(i) => this.handleSortEnd(i)}
                />
            </div>
        );
    }
}

const Track = SortableElement(({
    // Track props
    track,
    isFirstTrack,
    playStartTime,
    playCurrentTime,
    onTrackRemove
}) => {
    let playTimeRemaining = Math.max(track.duration - track.offset, 0);
    if (isFirstTrack) {
        playTimeRemaining = Math.max(
            track.duration - track.offset - (playCurrentTime - playStartTime) / 1000,
            0
        );
    }
    const playTimeProgress = track.live ?
        0.0 :
        1.0 - playTimeRemaining / Math.max(track.duration, 1.0);

    return (
        <li className="LivePlaylist-Track">
            <div className="Metadata">
                <img className="Thumbnail" src={track.thumbnail}/>
                <div className="TrackInfo">
                    <div className="TrackTitle">
                        {track.title}
                    </div>
                    <div className="TrackDuration">
                        {track.live ? "Live" : TimestampFormat(playTimeRemaining)}
                    </div>
                </div>
                {track.url.length > 0 &&
                    <a
                        className="TrackUrl DragCancel"
                        href={track.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        onDragStart={(e) => e.preventDefault()}
                    >
                        <i className="fab fa-youtube DragCancel"></i>
                    </a>
                }
                <button
                    className="DragCancel"
                    onClick={() => onTrackRemove(track.id)}
                >
                    <i className="fas fa-times DragCancel"></i>
                </button>
            </div>
            <div className="Progress" style={{width: `${playTimeProgress * 100}%`}}></div>
        </li>
    );
});

const Playlist = SortableContainer(({
    // Playlist props
    tracks,
    playStartTime,
    playCurrentTime,
    onTrackRemove
}) => {
    const trackList = tracks.map((track, index) =>
        <CSSTransition
            key={track.id}
            timeout={100}
            classNames="LivePlaylist-Track"
        >
            <Track
                key={track.id}
                index={index}
                track={track}
                isFirstTrack={index == 0}
                playStartTime={playStartTime}
                playCurrentTime={playCurrentTime}
                onTrackRemove={onTrackRemove}
            />
        </CSSTransition>
    );
    return (
        <TransitionGroup component={"ol"}>
            {trackList}
        </TransitionGroup>
    );
});

LivePlaylist.propTypes = {
    eventDispatcher: PropTypes.instanceOf(Message.EventDispatcher).isRequired,
    socket: PropTypes.instanceOf(WebSocket).isRequired
};
