const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const config = require("../config.json");

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
            bot_url: `wss://${config.bot_domain}:${config.bot_port}`
        })
    ],
    externals: {
        config: JSON.stringify({
            "client_url": `https://${config.client_domain + (config.client_port == 80 ? "" : ":" + config.client_port)}`
        })
    },
    devServer: {
        contentBase: "./build"
    }
};
