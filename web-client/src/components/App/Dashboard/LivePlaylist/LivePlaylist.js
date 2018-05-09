// --- LivePlaylist.js ---------------------------------------------------------
// Component for viewing queued music

import "./LivePlaylist.scss";

import React from "react";
import {SortableContainer, SortableElement, arrayMove} from "react-sortable-hoc";
import * as Message from "utils/Message";
import TimestampFormat from "utils/TimestampFormat";

export default class LivePlaylist extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            queue: Array(),
            animatingEnter: Array(),
            animatingExit: Array(),
            playCurrentTime: 0
        };
        this.animatingTasks = new Set();

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
                    break;
            }
        });
        // Request the initial queue state
        this.props.socket.send(new Message.PlayQueueGetMessage().str());
        this.props.socket.send(new Message.PlayStatusGetMessage().str());
    }

    componentWillUnmount() {
        this.props.eventDispatcher.clearMessageHandler("play.queue.send");
        this.props.eventDispatcher.clearMessageHandler("play.status.send");

        this.setState({
            queue: Array(),
            animatingEnter: Array(),
            animatingExit: Array()
        });

        for (let task of this.animatingTasks) {
            clearTimeout(task);
        }
        this.animatingTasks.clear();

        this.pausePlayProgress();
    }

    // Manually manage CSS transition animations, as react-sortable-hoc breaks react-transition-groups
    // Hacky, dirty, but not too much added code and overall less janky feeling than no animations
    handleQueueChange(newQueue) {
        // Shove states into a Set for (presumably) fast lookups
        const oldIds = new Set(this.state.queue.map(t => t.id));
        const newIds = new Set(newQueue.map(t => t.id));
        // Generate diffs of the 2 queues
        const addedItems = newQueue.filter(t => !oldIds.has(t.id));
        const removedItems = this.state.queue.filter(t => !newIds.has(t.id));
        const addedIds = new Set(addedItems.map(t => t.id));
        const removedIds = new Set(removedItems.map(t => t.id));
        // Immediately append the newly added items for enter animations
        this.setState({
            queue: this.state.queue.concat(addedItems),
            animatingEnter: this.state.animatingEnter.concat([...addedIds]),
            animatingExit: this.state.animatingExit.concat([...removedIds])
        });
        const timeoutId = setTimeout(() => {
            // Fully update the state (sub removedItems) once exit animations have been completed
            this.setState({
                queue: newQueue,
                animatingEnter: this.state.animatingEnter.filter(id => !addedIds.has(id)),
                animatingExit: this.state.animatingExit.filter(id => !removedIds.has(id))
            });
            this.animatingTasks.delete(timeoutId);
            // Reset play progress once the new track offsets take hold
            this.resetPlayProgress();
        }, 100);
        this.animatingTasks.add(timeoutId);
    }

    handleSortStart() {
        this.skipPlayUpdateTask = true;
    }

    handleSortEnd({oldIndex, newIndex}) {
        this.skipPlayUpdateTask = false;
        this.queueMove(oldIndex, newIndex);
    }

    queueMove(oldIndex, newIndex) {
        const trackId = this.state.queue[oldIndex].id;
        // Update server
        this.props.socket.send(new Message.PlayQueueMoveMessage(trackId, newIndex).str());
        // Predictively update client
        this.setState({
            queue: arrayMove(this.state.queue, oldIndex, newIndex)
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
                    animatingEnterList={this.state.animatingEnter}
                    animatingExitList={this.state.animatingExit}
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
        isAnimatingEnter,
        isAnimatingExit,
        isFirstTrack,
        playStartTime,
        playCurrentTime,
        onTrackRemove
    }) => {
    let classes = ["LivePlaylist-Track"];
    if (isAnimatingExit) {
        classes.push("LivePlaylist-Track-Exit");
    } else if (isAnimatingEnter) {
        classes.push("LivePlaylist-Track-Enter");
    }

    let playTimeRemaining = Math.max(track.duration - track.offset, 0);
    if (isFirstTrack) {
        playTimeRemaining = Math.max(
            track.duration -
            track.offset -
            (playCurrentTime - playStartTime) / 1000,
        0);
    }
    playTimeRemaining = Math.trunc(playTimeRemaining);
    const playTimeProgress = 1.0 - playTimeRemaining / Math.max(track.duration, 1.0);

    return (
        <li className={classes.join(" ")}>
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
        animatingEnterList,
        animatingExitList,
        playStartTime,
        playCurrentTime,
        onTrackRemove
    }) => {
    const trackList = tracks.map((track, index) =>
        <Track
            key={track.id}
            index={index}
            track={track}
            isAnimatingEnter={animatingEnterList.includes(track.id)}
            isAnimatingExit={animatingExitList.includes(track.id)}
            isFirstTrack={index == 0}
            playStartTime={playStartTime}
            playCurrentTime={playCurrentTime}
            onTrackRemove={onTrackRemove}
        />
    );
    return (
        <ol>
            {trackList}
        </ol>
    );
});
