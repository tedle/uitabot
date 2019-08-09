// --- Login.js ----------------------------------------------------------------
// Login form

import "./Login.scss";

import React from "react";
import PropTypes from "prop-types";

export default function Login({url}) {
    return (
        <div className="Login">
            <h1>uitabot</h1>
            <a href={url}>Login with <span className="Logo"></span></a>
        </div>
    );
}

Login.propTypes = {
    url: PropTypes.string.isRequired
};
