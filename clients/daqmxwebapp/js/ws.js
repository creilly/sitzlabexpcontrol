var WS_URL = 'ws://localhost:8888/ws';

var ws;

var callbacks = {};
var _callbackCounter = 0;
function sendCommand (command,data,callback) {
    if (data==undefined) data = {};
    var callbackID;
    if (callback==undefined) {
	callbackID = null;
    }
    else {
	callbackID = _callbackCounter++;
	callbacks[callbackID] = callback;
    }    
    ws.send(
	JSON.stringify(
	    {
		'command':command, 
		'data':data, 
		'callback':callbackID
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

function onClose (evt)  { 
    console.log('connection closed');
};

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
    callbacks[data.id](data.data)
}
handlers['callback'] = onCallback;
function onError(data) {
    createNotification(data);
}
handlers['error'] = onError;

$(document).ready(onReady);
