// --- Error.js ----------------------------------------------------------------
// Fatal error display component

import "./Error.scss";

import React from "react";

const Context = React.createContext(() => {});
export {Context};

export function Fatal({children}) {
    return (
        <div className="Error">
            <i className="fas fa-times"></i> {children}
        </div>
    );
}
