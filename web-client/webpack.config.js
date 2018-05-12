const path = require("path");
const CleanWebpackPlugin = require("clean-webpack-plugin");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const OptimizeCssAssetsPlugin = require("optimize-css-assets-webpack-plugin");
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
            assets: path.resolve(__dirname, "src/assets"),
            components: path.resolve(__dirname, "src/components"),
            styles: path.resolve(__dirname, "src/styles"),
            utils: path.resolve(__dirname, "src/utils")
        }
    },
    output: {
        filename: "assets/[contenthash].js",
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
                use: [MiniCssExtractPlugin.loader, "css-loader", "sass-loader"],
                exclude: /node_modules/
            },
            {
                test: /\.svg$/,
                use: "url-loader",
                exclude: /node_modules/
            }
        ]
    },
    plugins: [
        new CleanWebpackPlugin(["build"]),
        new HtmlWebpackPlugin({
            template: "./src/index.html",
            filename: "./index.html",
            bot_url: bot_url
        }),
        new MiniCssExtractPlugin({ filename: "assets/[contenthash].css" }),
        new OptimizeCssAssetsPlugin({
            cssProcessorOptions: { reduceIdents: false }
        })
    ],
    externals: {
        config: JSON.stringify({
            "client_id": config.discord.client.id,
            "youtube_api": config.youtube.api_key,
            "bot_url": bot_url,
            "client_url": client_url
        })
    },
    devtool: "none",
    devServer: {
        contentBase: "./build",
        host: config.client.domain,
        port: config.client.port
    }
};
