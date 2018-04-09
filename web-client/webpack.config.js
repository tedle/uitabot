const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const ExtractTextPlugin = require("extract-text-webpack-plugin");
const config = require("../config.json");

const bot_url = `ws${config.ssl.cert_file.length > 0 ? "s" : ""}://`
                + `${config.bot.domain}`
                + `${config.bot.port == 80 ? "" : ":" + config.bot.port}`;
const client_url = `http${config.ssl.cert_file.length > 0 ? "s" : ""}://`
                   + `${config.client.domain}`
                   + `${config.client.port == 80 ? "" : ":" + config.client.port}`;

module.exports = {
    entry: ["./src/index.js"],
    resolve: {
        alias: {
            components: path.resolve(__dirname, "src/components"),
            utils: path.resolve(__dirname, "src/utils")
        }
    },
    output: {
        filename: "app.js",
        path: path.resolve(__dirname, "build")
    },
    module: {
        rules: [
            {
                test: /\.js$/,
                use: "babel-loader",
                exclude: /node_modules/
            },
            {
                test: /\.scss$/,
                use: ExtractTextPlugin.extract({
                    use: ["css-loader", "sass-loader"]
                }),
                exclude: /node_modules/
            }
        ]
    },
    plugins: [
        new HtmlWebpackPlugin({
            template: "./src/index.html",
            filename: "./index.html",
            bot_url: bot_url
        }),
        new ExtractTextPlugin("styles.css")
    ],
    externals: {
        config: JSON.stringify({
            "client_id": config.discord.client.id,
            "youtube_api": config.youtube.api_key,
            "bot_url": bot_url,
            "client_url": client_url
        })
    },
    devServer: {
        contentBase: "./build"
    }
};
