import * as QueryString from "query-string";
import * as Message from "./message.js";

export default function authenticate(socket) {
    const query = QueryString.parse(location.search);
    if ('code' in query) {
        socket.send(new Message.AuthTokenMessage(code).str());
    }
    socket.send(new Message.AuthSessionMessage("12345", "me").str());
}
