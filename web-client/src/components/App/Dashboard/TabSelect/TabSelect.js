// --- TabSelect.js ------------------------------------------------------------
// Component for displaying Dashboard tab selection

import "./TabSelect.scss";

import React from "react";

export default function TabSelect(props) {
    const tabs = props.tabs.map(tab => {
        const classes = tab.id == props.active ? "Active" : "";
        return (
            <button key={tab.id} className={classes} onClick={() => props.onSelect(tab.id)}>
                {tab.display}
            </button>
        );
    });
    return (
        <div className="TabSelect">
            {tabs}
        </div>
    );
}
