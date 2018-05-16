// --- TouchButton.js ----------------------------------------------------------
// Component that adds a wasTapped boolean property to button onClick events
//
// JavaScript has no good means for detecting if a click event was triggered by
// touch or not. Simply using touchend or touchstart will trigger when
// swiping/scrolling so we must also listen for touchmove events and record
// their state for any given sequence of touch events.
// Life on the web is never ending terror.

import React from "react";

export default class TouchButton extends React.Component {
    componentDidMount() {
        this.resetTapDetection();
    }

    componentWillUnmount() {
        this.resetTapDetection();
    }

    resetTapDetection() {
        this._tapEventDetection = {
            moved: false,
            tapped: false
        };
    }

    forwardEvent(eventName, event) {
        if (eventName in this.props) {
            this.props[eventName](event);
        }
    }

    handleClick(event) {
        // React complains when you modify events because they are pooled and re-used, making it
        // so they are not safe to access asynchronously. And even though we're not doing that,
        // we still get false alarm warning messages. So we persist the event and remove it from
        // the event pool just to get around an irrelevant, but annoying, warning message.
        event.persist();
        event.wasTapped = this._tapEventDetection.tapped;
        this._tapEventDetection.tapped = false;
        this.forwardEvent("onClick", event);
    }

    handleTouchMove(event) {
        this._tapEventDetection.moved = true;
        this.forwardEvent("onTouchMove", event);
    }

    handleTouchEnd(event) {
        if (!this._tapEventDetection.moved) {
            this._tapEventDetection.tapped = true;
        }
        this._tapEventDetection.moved = false;
        this.forwardEvent("onTouchEnd", event);
    }

    handleTouchCancel(event) {
        this._tapEventDetection.moved = false;
        this.forwardEvent("onTouchCancel", event);
    }

    render() {
        // Unpacked props must be listed first so that our wrapped props can override them
        return (
            <button
                {...this.props}
                onClick={e => this.handleClick(e)}
                onTouchMove={e => this.handleTouchMove(e)}
                onTouchEnd={e => this.handleTouchEnd(e)}
                onTouchCancel={e => this.handleTouchCancel(e)}
            />
        );
    }
}
