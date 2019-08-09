// --- Header.js ---------------------------------------------------------------
// Component for displaying Dashboard header

import "./Header.scss";

import React from "react";
import PropTypes from "prop-types";
import * as Session from "utils/Session";

export default function Header(props) {
    return (
        <div className="Header">
            <h1>{props.discordServer.name}</h1>
            <img className="Avatar" src={props.discordUser.avatar}/>
            <div className="Username hidden-xs">
                {props.discordUser.name}
            </div>
            <button className="Logout" onClick={Session.logout}>
                <i className="fas fa-sign-out-alt"></i>
            </button>
        </div>
    );
}

Header.propTypes = {
    discordServer: PropTypes.shape({
        name: PropTypes.string
    }).isRequired,
    discordUser: PropTypes.shape({
        avatar: PropTypes.string,
        name: PropTypes.string
    }).isRequired
};
