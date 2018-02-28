// --- message.js --------------------------------------------------------------
// Utility classes for parsing and building network packets
// For detailed breakdown on protocol uses, see /bot/uita/message.py

// Abstract base class for network messages
export class AbstractMessage {
    static get header() {
        return "base";
    }

    // Serializes object for network transfer
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

    constructor(handle, secret) {
        super();
        this.handle = handle;
        this.secret = secret;
    }
}

export class AuthSucceedMessage extends AbstractMessage {
    static get header() {
        return "auth.succeed";
    }

    constructor(username, session_handle, session_secret) {
        super();
        this.username = username;
        this.session_handle = session_handle;
        this.session_secret = session_secret;
    }
}

export class ChannelListGetMessage extends AbstractMessage {
    static get header() {
        return "channel.list.get";
    }
}

export class ChannelListSendMessage extends AbstractMessage {
    static get header() {
        return "channel.list.send";
    }

    constructor(channels) {
        super();
        this.channels = channels;
    }
}

export class HeartbeatMessage extends AbstractMessage {
    static get header() {
        return "heartbeat";
    }
}

export class PlayURLMessage extends AbstractMessage {
    static get header() {
        return "play.url";
    }

    constructor(url) {
        super();
        this.url = url;
    }
}

export class ServerKickMessage extends AbstractMessage {
    static get header() {
        return "server.kick";
    }
}

export class ServerJoinMessage extends AbstractMessage {
    static get header() {
        return "server.join";
    }

    constructor(server_id) {
        super();
        this.server_id = server_id;
    }
}

export class ServerListGetMessage extends AbstractMessage {
    static get header() {
        return "server.list.get";
    }
}

export class ServerListSendMessage extends AbstractMessage {
    static get header() {
        return "server.list.send";
    }

    constructor(servers) {
        super();
        this.servers = servers;
    }
}

// Hash map linking message headers to class constructors, along with expected input values
const VALID_MESSAGES = {
    "auth.code": [AuthCodeMessage, ["code"]],
    "auth.fail": [AuthFailMessage, []],
    "auth.session": [AuthSessionMessage, ["handle", "secret"]],
    "auth.succeed": [AuthSucceedMessage, ["username", "session_handle", "session_secret"]],
    "channel.list.get": [ChannelListGetMessage, []],
    "channel.list.send": [ChannelListSendMessage, ["channels"]],
    "heartbeat": [HeartbeatMessage, []],
    "play.url": [PlayURLMessage, ["url"]],
    "server.kick": [ServerKickMessage, []],
    "server.join": [ServerJoinMessage, ["server_id"]],
    "server.list.get": [ServerListGetMessage, []],
    "server.list.send": [ServerListSendMessage, ["servers"]]
};

// Translates input messages into client callbacks
export class EventDispatcher {
    constructor() {
        this.handlers = [];
    }

    setMessageHandler(header, handler) {
        this.handlers[header] = handler;
    }

    clearMessageHandler(header) {
        delete this.handlers[header];
    }

    dispatch(message) {
        if (!message instanceof AbstractMessage) {
            throw new TypeError("EventDispatcher.dispatch requires a subclass of AbstractMessage");
        }

        // Javascript makes you access an instances constructor to get at its static methods
        // whats up with that?
        const header = message.constructor.header;
        if (header in this.handlers) {
            this.handlers[header](message);
        }
    }
}

// Turns raw network data into Message classes
export function parse(message) {
    let obj = JSON.parse(message);
    let args = Array();
    // Verify that the expected arguments match with what is in the message
    for (let arg of VALID_MESSAGES[obj.header][1]) {
        if (arg in obj) {
            args.push(obj[arg]);
        }
        else {
            throw new TypeError("Mismatched parmeters between parsed message and associated type");
        }
    }
    // Call the aproppriate constructor with our array of arguments
    // This is what modern javascript looks like
    return new (Function.prototype.bind.call(VALID_MESSAGES[obj.header][0], null, ...args));
}
