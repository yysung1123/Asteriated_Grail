import {Terminal} from 'xterm';
import { AttachAddon } from 'xterm-addon-attach';

const socketUrl = 'ws://localhost:12345'
const webSocket = new WebSocket(socketUrl);

const term = new Terminal({cols: 80, rows: 24, disableStdin: true, convertEol: true});
const attachAddon = new AttachAddon(webSocket);
term.loadAddon(attachAddon);

const container = document.getElementById('terminal');
term.open(container);
term.setOption('disableStdin', true);

const input = document.getElementById('input');
input.addEventListener('keyup', function(e) {
    if (e.keyCode == 13) {
        webSocket.send(e.target.value)
    }
})
