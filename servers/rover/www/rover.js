function initialize() {
    initRover();
    sendCommand('subscribe',{'name':'samples'});
    sendCommand('subscribe',{'name':'write'});
    sendCommand('subscribe',{'name':'change'});
    bindControls();
}

function bindControls() {
    function getID(DOM) {return $(DOM).parents('[eID]').attr('eID');}
    function btnBool(DOM) {return $(DOM).hasClass('active');}
    $('[rover-mode]').click(
	function () {	    
	    if (!btnBool(this))	{
		setProperty(
		    'switch',
		    getID(this),
		    'mode',
		    $(this).attr('rover-mode') == 'interlock'
		);
	    }		
	}
    );
    var toggles = ['user','interlock','fail'];
    for (var property in toggles) {
	$('.' + toggles[property] + '-state').click(
	    function(property) {
		return function () {
		    setProperty(
			'switch',
			getID(this),
			toggles[property],
			!btnBool(this)
		    )
		}
	    }(property)
	)
    }
};

function setProperty(eType,id,property,value) {
    sendCommand(
	'set property',
	{
	    'element':eType,
	    'id':id,
	    'property':property,
	    'value':value,
	}
    );
}

var roverState;

function onChange(eType,id,property,value) {
    console.log(eType + ' ' + id + ' ' + property + ' ' + value.toString() );
    var d = {
	'switch':switchChanged,
	'sensor':sensorChanged,
	'interlock':interlockChanged
    };
    d[eType](get$(id),property,value);
}
handlers['change'] = function(data) {
    onChange(data.element,data.id,data.property,data.value);
}

function switchChanged(Switch,property,value) {
    switch (property) {
	case 'user': {
	    Switch
		.find('.user-state')
		.toggleClass('active',value)
		.text(value ? 'engaged' : 'disabled');
	    break;
	}
	case 'interlock': {
	    Switch
		.find('.interlock-state')
		.toggleClass('active',value)
		.text(value ? 'engaged' : 'disabled');
	    break;
	}
	case 'fail': {
	    Switch
		.find('.fail-state')
		.toggleClass('active',value)
		.text(value ? 'fail' : 'ok');
	    break;
	}
	case 'mode': {
	    var d = {true:'interlock',false:'user'};	    
	    Switch.find(
		'[' + 'rover-mode' + '=' + d[value] + ']'
	    ).addClass('active');
	    Switch.find(
		'[' + 'rover-mode' + '=' + d[!value] + ']'
	    ).removeClass('active');
	    break;
	}	
    }    
};

function interlockChanged(interlock,property,value) {
    switch (property) {
	case 'threshold': {
	    break;
	}
	case 'defeated': {
	    break;
	}
    }
}

function sensorChanged(sensor,property,value) {
    return;
}

function initRover() {
    sendCommand(
	'get state',
	{},
	function (state) {
	    // for (var eType in state) {
	    // 	for (var id in state[eType]) {
	    // 	    for (var property in state[eType][id]) {
	    // 		onChange(eType,id,property,state[eType][id][property]);
	    // 	    }
	    // 	}
	    // }
	    console.log(state);
	    for (var id in state['switch']) {
		var props = ['mode','user','interlock','fail'];
	    	for (var property in props) {
	    	    onChange('switch',id,props[property],state['switch'][id][props[property]]);
	    	}
	    }
	    
	    function getCB(s) {
		return function (b) {
		    get$(s).find('.state').addClass(b ? 'on' : 'off').text(b ? 'on' : 'off');
		}
	    }

	    for (var id in state['switch']) {
		sendCommand('get computed',{'switch':id},getCB(id));
	    }
	}
    );
}

function onSamples(samples) {
    for (var sensor in samples) {
	get$(sensor).find('.sample').text(samples[sensor].toFixed(2));
	d3.select(get$(sensor).find('rect')[0]).attr('width',300.0 * samples[sensor] / 5.0 );
    }
}
handlers['samples'] = onSamples;

function onWrite(swatch,state){
    var stateWidget = get$(swatch).find('.state');
    if (stateWidget.hasClass(state ? 'off' : 'on')) {
	stateWidget.toggleClass('on').toggleClass('off').text(state ? 'on' : 'off');
    }
    console.log(swatch + ' -> ' + ( state ? 'on' : 'off' ));
}
handlers['write'] = function (data) {onWrite(data.switch,data.state)};

function get$(id) {return $('[eID=' + id + ']')};

