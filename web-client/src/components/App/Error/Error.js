// --- Error.js ----------------------------------------------------------------
// Components for displaying fatal errors or a list of error-related popups

import "./Error.scss";

import React from "react";
import {CSSTransition, TransitionGroup} from "react-transition-group";

const Context = React.createContext(() => {});
export {Context};

export function Fatal({children}) {
    return (
        <div className="Error">
            <i className="fas fa-times"></i> {children}
        </div>
    );
}

export class List extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
        };
    }

    render() {
        const errors = this.props.errors.map(error => {
            return (
                <CSSTransition
                    key={error.id}
                    timeout={300}
                    classNames="Error-List-Item"
                >
                    <li key={error.id} className="Error-List-Item">
                        <div className="Error-Message">
                            {error.message}
                        </div>
                        <button onClick={() => this.props.onRemove(error.id)}>
                            <i className="fas fa-times"></i>
                        </button>
                    </li>
                </CSSTransition>
            );
        });
        return (
            <div className="Error-List">
                <TransitionGroup component={"ul"}>
                    {errors}
                </TransitionGroup>
            </div>
        );
    }
}
