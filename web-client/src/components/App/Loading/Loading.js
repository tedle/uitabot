// --- Loading.js --------------------------------------------------------------
// Loading transition display component

import "./Loading.scss";

import React from "react";

export default function Loading({children}) {
    return (
        <div className="Loading">
            {children} <i className="fas fa-spinner fa-spin"></i>
        </div>
    );
}
