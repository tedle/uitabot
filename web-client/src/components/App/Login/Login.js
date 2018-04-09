// --- Login.js ----------------------------------------------------------------
// Login form

import "./Login.scss";

import React from "react";

export default function Login({url}) {
    return (
        <div className="Login">
            <h1>uitabot</h1>
            <a href={url}>Login with <span className="logo"></span></a>
        </div>
    );
}
