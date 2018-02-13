const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const config = require("../config.json");

const bot_url = `ws${config.ssl.cert_file.length > 0 ? "s" : ""}://`
                + `${config.bot_domain}`
                + `${config.bot_port == 80 ? "" : ":" + config.bot_port}`;
const client_url = `http${config.ssl.cert_file.length > 0 ? "s" : ""}://`
                   + `${config.client_domain}`
                   + `${config.client_port == 80 ? "" : ":" + config.client_port}`;

module.exports = {
    entry: ["./src/index.js"],
    output: {
        filename: "app.js",
        path: path.resolve(__dirname, "build")
    },
    module: {
        rules: [
            {
                use: "babel-loader",
                test: /\.js$/,
                exclude: /node_modules/
            }
        ]
    },
    plugins: [
        new HtmlWebpackPlugin({
            template: "./src/index.html",
            filename: "./index.html",
            bot_url: bot_url
        })
    ],
    externals: {
        config: JSON.stringify({
            "bot_url": bot_url,
            "client_url": client_url
        })
    },
    devServer: {
        contentBase: "./build"
    }
};
