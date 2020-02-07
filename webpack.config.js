path = require('path');
module.exports = {
    entry: './src/index.js',
    output: {
        filename: 'dist/bundle.js',
        path: path.resolve(__dirname, './')
    },
    devServer: {
        contentBase: path.join(__dirname, "./"),
        compress: true,
    }
};