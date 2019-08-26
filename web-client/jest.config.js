module.exports = {
    moduleDirectories: ["node_modules", "<rootDir>/test"],
    moduleNameMapper: {
        // Webpack aliases
        "^(assets|components|styles|utils)\\/(.*)$": "<rootDir>/src/$1/$2",
        // Webpack externals
        "^config$": "<rootDir>/test/config.mock.js",
        // CSS imports
        "\\.scss$": "<rootDir>/test/css.mock.js"
    },
    setupFilesAfterEnv: ["<rootDir>/test/crypto.mock.js"]
};
