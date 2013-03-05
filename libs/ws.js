var WS_URL = 'ws://localhost:8888/ws';

var ws;

var _counter = 0;
var callbacks = {};
function Callback(callback,errback) {
    this.callback = callback;
    this.errback = errback;
    this.id = _counter++;
}

function sendCommand (command,data,callback,errback) {
    if (callback===undefined) callback = function () {}
    if (errback===undefined) errback = printError('error');
    var callback = new Callback(callback,errback);
    callbacks[callback.id] = callback;
    ws.send(
	JSON.stringify(
	    {
		'command':command, 
		'data':data, 
		'callback':callback.id
	    }
	)
    );
};

function onReady () {
    openWebSocket();
};

function onOpen (evt) { 
    console.log('connection open');
    initialize();
};

//override this method
function initialize () {};

function onClose (evt)  { 
    console.log('connection closed');
    terminate();
};

//override this method
function terminate () {};

var handlers = {};
function onMessage (evt) {
    var message = JSON.parse(evt.data);
    for (var key in message) {
	if (key in handlers) {
	    handlers[key](message[key]);
	}
    }
};

function openWebSocket () {    

    ws = new WebSocket(WS_URL);
    
    ws.onmessage = onMessage;
    
    ws.onclose = onClose;
    
    ws.onopen = onOpen;

};

function onCallback(data) {
    callbacks[data.id].callback(data.data);
    delete callbacks[data.id];
}
handlers['callback'] = onCallback;


function onError(data) {
    callbacks[data.id].errback(data.message);
    delete callbacks[data.id];
}
handlers['error'] = onError;

$(document).ready(onReady);
