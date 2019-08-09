// --- TabSelect.js ------------------------------------------------------------
// Component for displaying Dashboard tab selection

import "./TabSelect.scss";

import React from "react";
import PropTypes from "prop-types";

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

TabSelect.propTypes = {
    tabs: PropTypes.arrayOf(PropTypes.shape({
        id: PropTypes.string,
        display: PropTypes.string
    })).isRequired,
    active: PropTypes.string.isRequired,
    onSelect: PropTypes.func.isRequired
};
