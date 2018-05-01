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
            queue: Array()
        };
    }

    componentDidMount() {
        // Once mounted, bind the event dispatchers callback for play queue queries
        this.props.eventDispatcher.setMessageHandler("play.queue.send", m => {
            this.setState({queue: m.queue})
        });
        // Request the initial queue state
        this.props.socket.send(new Message.PlayQueueGetMessage().str());
    }

    componentWillUnmount() {
        this.props.eventDispatcher.clearMessageHandler("play.queue.send");
    }

    queueMove({oldIndex, newIndex}) {
        const track_id = this.state.queue[oldIndex].id;
        // Update server
        this.props.socket.send(new Message.PlayQueueMoveMessage(track_id, newIndex).str());
        // Predictively update client
        this.setState({
            queue: arrayMove(this.state.queue, oldIndex, newIndex)
        });
    }

    queueRemove(track_id) {
        this.props.socket.send(new Message.PlayQueueRemoveMessage(track_id).str());
    }

    render() {
        const Track = SortableElement(({track}) => {
            return (
                <li className="LivePlaylist-Track">
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
