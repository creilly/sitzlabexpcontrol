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
    bindControls();
};

function onOpen (evt) { 
    sendCommand('devices',{},onDevices);
};

function onClose (evt)  { 
    console.log('connection closed');
};

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

function bindControls () {
    $('#device').change(function () {
	sendCommand(
	    'physical channels',
	    {'device':selectedDevice()},
	    onPhysicalChannels
	);
    });

    $('#add-acq').click(function () {
	var name = selectedName();
	var device = selectedDevice();
	var channel = selectedChannel();
	sendCommand(
	    'tasks',
	    {},
	    function (tasks) {
		if ($.inArray(name,tasks) >= 0) {
		    createNotification('"' + name + '"' + ' name already taken' );
		    return
		}
		createAcq(name, device, channel);
	    }
	);
    });
};

function close () {
    ws.close();
};

function selectedDevice () {
    return $('#device > option:selected').prop('value');
}

function selectedChannel () {
    return $('#channel > option:selected').prop('value');
}

function selectedName() {
    return $('#name').prop('value');
}

function createAcq (name, device, channel) {
    var physicalChannel = device + '/' + channel;

    sendCommand('create task',{'name':name});
    sendCommand(
	'create channel',
	{
	    'task':name,
	    'physicalChannel':physicalChannel,
	    'name':'na'
	}
    );

    function onSample (sample) {
	$('.value',tr).text(sample.toFixed(2));
    };

    var timer = setInterval(
	function(){	    
	    sendCommand('read sample', {'task':name}, onSample)
	}
	,100
    );

    var tr = $('<tr>')
	.attr('name',name)
	.append(
	    $('<td>').text(name)
	)
	.append(
	    $('<td>').text(device)
	)
	.append(
	    $('<td>').text(channel)
	)	
	.append(
	    $('<td>').addClass('value').text('na')
	)
	.append(
	    $('<td>').append(
		$('<button>')
		    .addClass('plain')
		    .text('remove')
		    .click(function () {
			$(this).parents('tr').detach();
			clearInterval(timer);
			sendCommand('clear task',{'task':name});
		    })
	    )
	);

    $('#acqs > tbody').prepend(tr);    
}

var handlers = {};

function onCallback(data) {
    callbacks[data.id](data.data)
}
handlers['callback'] = onCallback;
function onError(data) {
    createNotification(data);
}
handlers['error'] = onError;

function createNotification(message) {
    $('#notifications').prepend(
	$('<div>')	
	    .addClass('alert')
	    .addClass('notification')	
	    .append(
		$('<button>')
		    .addClass('close')
		    .attr('data-dismiss','alert')
		    .text('\xD7')
	    )
	    .append(
		$('<strong>')
		    .text('Error:')
	    )
	    .append(
		$('<span>')
		    .text(message)
	    )
    );
}

function onDevices (data) {
    $('#device').empty();
    $.each(data,function (index,value) {
	var option = $('<option>').prop('value',value).prop('label',value);
	$('#device').append(option);
	if (index == 0) {
	    option.select();
	}
    });
    $('#device').change();
};

function physicalChannels (device) {
    cbid = getCallbackID();
    sendCommand('physical channels',{'device':device},onPhysicalChannels,cbid);
};
function onPhysicalChannels (data) {
    $('#channel').empty();
    $.each(data, function(index, value) {
	$('#channel').append(
	    $('<option>').prop('value',value).prop('label',value)
	);
    });
};

$(document).ready(onReady);
