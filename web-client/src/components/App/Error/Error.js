// --- Error.js ----------------------------------------------------------------
// Fatal error display component

import "./Error.scss";

import React from "react";

export default function Error({children}) {
    return (
        <div className="Error">
            <i className="fas fa-times"></i> {children}
        </div>
    );
}
