// --- LivePlaylist.js ---------------------------------------------------------
// Component for viewing queued music

import "./LivePlaylist.scss";

import React from "react";
import {SortableContainer, SortableElement, arrayMove} from "react-sortable-hoc";
import * as Message from "utils/Message";

export default class LivePlaylist extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            queue: Array(),
            animatingEnter: Array(),
            animatingExit: Array()
        };
        this.animatingTasks = new Set();
    }

    componentDidMount() {
        // Once mounted, bind the event dispatchers callback for play queue queries
        this.props.eventDispatcher.setMessageHandler("play.queue.send", m => {
            this.handleQueueChange(m.queue);
        });
        // Request the initial queue state
        this.props.socket.send(new Message.PlayQueueGetMessage().str());
    }

    componentWillUnmount() {
        this.props.eventDispatcher.clearMessageHandler("play.queue.send");

        this.setState({
            queue: Array(),
            animatingEnter: Array(),
            animatingExit: Array()
        });

        for (let task of this.animatingTasks) {
            clearTimeout(task);
        }
        this.animatingTasks.clear();
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
        }, 100);
        this.animatingTasks.add(timeoutId);
    }

    queueMove({oldIndex, newIndex}) {
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

    render() {
        const Track = SortableElement(({track}) => {
            let classes = ["LivePlaylist-Track"];
            if (this.state.animatingExit.includes(track.id)) {
                classes.push("LivePlaylist-Track-Exit");
            } else if (this.state.animatingEnter.includes(track.id)) {
                classes.push("LivePlaylist-Track-Enter");
            }
            return (
                <li className={classes.join(" ")}>
                    <img className="Thumbnail" src={track.thumbnail}/>
                    <div className="TrackTitle">
                        {track.title}
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
                        onClick={() => this.queueRemove(track.id)}
                    >
                        <i className="fas fa-times DragCancel"></i>
                    </button>
                </li>
            );
        });

        const Playlist = SortableContainer(({tracks}) => {
            const a = tracks.map((track, index) =>
                <Track key={track.id} index={index} track={track}/>
            );
            return (
                <ol>
                    {a}
                </ol>
            );
        });

        return (
            <div className="LivePlaylist">
                <Playlist
                    tracks={this.state.queue}
                    shouldCancelStart={(e) => e.target.classList.contains("DragCancel")}
                    onSortEnd={(i) => this.queueMove(i)}
                />
            </div>
        );
    }
}
