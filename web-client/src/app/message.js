export class AbstractMessage {
    static get header() {
        return "base";
    }

    str() {
        let obj = Object();
        obj.header = this.constructor.header;
        for(let property in this) {
            obj[property] = String(this[property]);
        }
        return JSON.stringify(obj);
    }
}

export class AuthCodeMessage extends AbstractMessage {
    static get header() {
        return "auth.code";
    }

    constructor(code) {
        super();
        this.code = code;
    }
}

export class AuthFailMessage extends AbstractMessage {
    static get header() {
        return "auth.fail";
    }
}

export class AuthSessionMessage extends AbstractMessage {
    static get header() {
        return "auth.session";
    }

    constructor(session, name) {
        super();
        this.session = session;
        this.name = name;
    }
}

export class AuthSucceedMessage extends AbstractMessage {
    static get header() {
        return "auth.succeed";
    }

    constructor(username, session_id, session_name) {
        super();
        this.username = username;
        this.session_id = session_id;
        this.session_name = session_name;
    }
}

const VALID_MESSAGES = {
    "auth.code": [AuthCodeMessage, ["code"]],
    "auth.fail": [AuthFailMessage, []],
    "auth.session": [AuthSessionMessage, ["session","name"]],
    "auth.succeed": [AuthSucceedMessage, ["username", "session_id", "session_name"]]
};

export class EventDispatcher {
    constructor() {
        this.onAuthFail = m => {}
        this.onAuthSucceed = m => {}
    }

    dispatch(message) {
        if (!message instanceof AbstractMessage) {
            throw new TypeError("EventDispatcher.dispatch requires a subclass of AbstractMessage");
        }
        switch(message.constructor) {
            case AuthFailMessage:
                this.onAuthFail(message);
                break;
            case AuthSucceedMessage:
                this.onAuthSucceed(message);
                break;
            default:
                throw new InternalError("EventDispatcher.dispatch has not implemented this message");
                break;
        }
    }
}

export function parse(message) {
    let obj = JSON.parse(message);
    let args = Array();
    for (let arg of VALID_MESSAGES[obj.header][1]) {
        if (arg in obj) {
            args.push(obj[arg]);
        }
        else {
            throw new TypeError("Mismatched parmeters between parsed message and associated type");
        }
    }
    // This is what modern javascript looks like
    return new (Function.prototype.bind.call(VALID_MESSAGES[obj.header][0], null, ...args));
}
