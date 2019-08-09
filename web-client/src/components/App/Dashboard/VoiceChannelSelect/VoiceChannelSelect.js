// --- VoiceChannelSelect.js ---------------------------------------------------
// Component for commanding bot to join voice channels

import "./VoiceChannelSelect.scss";

import React from "react";
import PropTypes from "prop-types";
import * as DiscordApi from "utils/DiscordApi";
import * as Message from "utils/Message";

export default class VoiceChannelSelect extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            channels: new Array(),
            activeChannelId: null,
            hiddenCategoryIds: new Set()
        };
    }

    componentDidMount() {
        // Once mounted, bind the event dispatchers callback for channel list queries
        this.props.eventDispatcher.setMessageHandler("channel.list.send", m => {
            this.setState({channels: m.channels});
        });
        this.props.eventDispatcher.setMessageHandler("channel.active.send", m => {
            if (m.channel !== null) {
                this.setState({activeChannelId: m.channel.id});
            } else {
                this.setState({activeChannelId: null});
            }
        });
        this.getChannelList();
    }

    componentWillUnmount() {
        this.props.eventDispatcher.clearMessageHandler("channel.list.send");
        this.props.eventDispatcher.clearMessageHandler("channel.active.send");
    }

    joinChannel(id) {
        this.props.socket.send(new Message.ChannelJoinMessage(id).str());
    }

    leaveChannel() {
        this.props.socket.send(new Message.ChannelLeaveMessage().str());
    }

    getChannelList() {
        this.props.socket.send(new Message.ChannelListGetMessage().str());
        this.props.socket.send(new Message.ChannelActiveGetMessage().str());
    }

    toggleCategoryHidden(id) {
        let categories = new Set(this.state.hiddenCategoryIds);
        if (categories.has(id)) {
            categories.delete(id);
        }
        else {
            categories.add(id);
        }
        this.setState({hiddenCategoryIds: categories});
    }

    isCategoryHidden(id) {
        return this.state.hiddenCategoryIds.has(id);
    }

    render() {
        const categoryList = this.state.channels
            .filter(channel => {
                // Make a list of category channels
                return channel.type == DiscordApi.ChannelType.GUILD_CATEGORY;
            })
            .map(category => {
                // Add accessible voice channels of each category into a sorted array
                return Object.assign({
                    channels: this.state.channels
                        .filter(channel => {
                            return (
                                channel.category == category.id &&
                                channel.type == DiscordApi.ChannelType.GUILD_VOICE
                            );
                        })
                        .sort((a, b) => {
                            return a.position - b.position;
                        })
                }, category);
            })
            .filter(category => {
                // Hide categories that have no accessible voice channels
                return category.channels.length > 0;
            })
            .sort((a, b) => {
                // Sort to match Discord UI order
                return a.position - b.position;
            })
            .map(category => {
                // Generate JSX elements
                const channelList = category.channels.map(channel => {
                    const activeClass = this.state.activeChannelId == channel.id ? "Active" : "";
                    return (
                        <li key={channel.id} className={activeClass}>
                            <button onClick={() => this.joinChannel(channel.id)}>
                                <i className="fas fa-volume-up"></i>
                                {channel.name}
                            </button>
                        </li>
                    );
                });

                const categoryClass = this.isCategoryHidden(category.id) ? "Hidden" : "";
                return (
                    <div className={categoryClass} key={category.id}>
                        <h2>
                            <button onClick={() => this.toggleCategoryHidden(category.id)}>
                                <i className="fas fa-angle-right"></i>
                                {category.name}
                            </button>
                        </h2>
                        <ul>{channelList}</ul>
                    </div>
                );
            });

        return (
            <div className="VoiceChannelSelect">
                {categoryList}
                {this.state.activeChannelId !== null &&
                    <div className="Disconnect">
                        <button onClick={() => this.leaveChannel()}>
                            <i className="fas fa-times"></i>
                            Disconnect
                        </button>
                    </div>
                }
            </div>
        );
    }
}

VoiceChannelSelect.propTypes = {
    eventDispatcher: PropTypes.instanceOf(Message.EventDispatcher).isRequired,
    socket: PropTypes.instanceOf(WebSocket).isRequired,
};
