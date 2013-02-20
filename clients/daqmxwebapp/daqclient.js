function Acquisition(name,device,channel) {
    this.name = name;
    this.device = device;
    this.channel = channel;

    this.data = [];
    this.timeout = 100;
    this.maxPoints = 100;

    this.recording = false;

    sendCommand('create task',{'name':this.name});
    sendCommand(
	'create channel',
	{
	    'task':this.name, 
	    'physicalChannel':(this.device + '/' + this.channel),
	    'name':'na'
	}
    );

    var self = this;
    this.tr = $('<tr>')
	.attr('name',this.name)
	.append(
	    $('<td>').text(this.name)
	)
	.append(
	    $('<td>').text(this.device)
	)
	.append(
	    $('<td>').text(this.channel)
	)	
	.append(
	    $('<td>').addClass('value').text('na')
	)
	.append(
	    $('<td>')
		.append(
		    $('<label>')
			.addClass('checkbox')
			.append(
			    $('<input>')
				.prop('type','checkbox')
				.addClass('plot')
				.change(function(){
				    if ($(this).is(':checked')) self.createPlot();
				    else self.removePlot();
				})
			)		    	
			.append(
			    $('<span>')
				.text('plot')
			)
		)
	)
	.append(
	    $('<td>')
		.append(
		    $('<button>')
			.addClass('plain')
			.addClass('record')
			.text('record')
			.click(self.startRecord.bind(self))
		)
	)
	.append(
	    $('<td>').append(
		$('<button>')
		    .addClass('plain')
		    .text('remove')
		    .click(function () {
			self.removeAcq();
		    })
	    )
	);


    $('#acqs > tbody').prepend(this.tr);    

    this.setSampleTimer();

};

Acquisition.prototype.startRecord = function () {
    var self = this;
    chrome.fileSystem.chooseEntry({'type':'saveFile'},function(fe){
	fe.createWriter(function(fw) {
	    console.log(fw.onwriteend);
	    fw.onerror = function () {console.log('error writing');}
	    fw.truncate(0);
	    fw.onwriteend = function () {
		console.log('truncation complete')
		self.fw = fw;
		self.recording = true;
		fw.onwriteend = null;
	    }

	});
    });

    $('button.record',this.tr)
	.text('recording...')
	.addClass('recording')
	.off('click')
	.click(this.stopRecord.bind(this))
}

Acquisition.prototype.stopRecord = function () {
    delete this.fw;
    this.recording = false;
    $('button.record',this.tr)
	.text('record')
	.removeClass('recording')
	.off('click')
	.click(this.startRecord.bind(this))
}

Acquisition.prototype.setSampleTimer = function () {
    this.timer = setTimeout(this.onTimeout.bind(this),this.timeout);
}

Acquisition.prototype.onSample = function (sample) {
    $('.value',this.tr).text(sample.toFixed(2));
    if (this.data.unshift(sample) > this.maxPoints) this.data.pop();
    if (this.plotting()) this.updatePlot();
    if (this.recording) this.fw.write(new Blob([sample.toFixed(3) + ', ']));
};

Acquisition.prototype.onTimeout = function () {
    var self = this;
    sendCommand('read sample', {'task':this.name}, this.onSample.bind(this))
    this.setSampleTimer();
};

Acquisition.prototype.plotting = function () {
    return $('.plot',this.tr).is(':checked')
}

Acquisition.prototype.createPlot = function () {
    console.log('creating plot');
    console.log(this.name);
    plotID = 'plot-' + this.name;
    this.tab = $('<li>')
	.append(
	    $('<a>')
		.prop('href','#' + plotID)
		.attr('data-toggle','tab')
		.text(this.name)
	);

    $('.nav').append( this.tab );

    this.div = $('<div>')
	.addClass('tab-pane')
	.prop('id',plotID)
    $('.tab-content').append(this.div);

    this.plot = d3.select('#' + plotID).append('svg');
    this.plot
	.classed('plot',true)
	.attr('width',400.0)
	.attr('height',400.0);

    $('a',this.tab).click();
};

Acquisition.prototype.updatePlot = function () {

    var WIDTH = 400.0;
    var HEIGHT = 400.0;
    var RADIUS = 2;
    var PADDING = .1;
    var Y_AXIS_PADDING = 0.0;
    var X_AXIS_PADDING = 0.0;

    var svg = this.plot;

    var data = this.data;

    var xScale = d3.scale.linear()
	.domain([data.length,0])
	.range([WIDTH * PADDING,WIDTH * ( 1.0 - PADDING )]);

    var yScale = d3.scale.linear()
	.domain(d3.extent(data))
	.range([HEIGHT * ( 1.0 -PADDING ), HEIGHT * PADDING]);

    var xAxisScale = d3.scale.linear()
	.range(yScale.range());
    
    var yAxisScale = d3.scale.linear()
	.range(xScale.range());

    //Define X  axis
    var xAxis = d3.svg.axis()
	.scale(xScale)
	.orient("bottom")
	.ticks(5);

    svg.selectAll('g').remove();

    svg.append("g")
	.attr("class", "axis")
	.attr("transform", "translate(0," + xAxisScale(X_AXIS_PADDING) + ")")
	.call(xAxis);

    //Define Y axis
    var yAxis = d3.svg.axis()
	.scale(yScale)
	.orient("left")
	.ticks(5);

    svg.append("g")
	.attr("class", "axis")
	.attr("transform", "translate(" + yAxisScale(Y_AXIS_PADDING) + ",0)")
	.call(yAxis);

    svg.selectAll('circle').remove();

    svg.selectAll('circle')
	.data(data)
	.enter()
	.append('circle')
	.attr('cx',function(d,i){return xScale(i)})
	.attr('cy',function(d){return yScale(d)})
	.attr('r',RADIUS);

};

Acquisition.prototype.removePlot = function () {
    console.log('removing plot');
    this.tab.detach();
    this.plot.remove();
};

Acquisition.prototype.removeAcq = function () {
    if (this.plotting()) this.removePlot();    
    this.tr.detach();
    clearInterval(this.timer);
    sendCommand('clear task',{'task':this.name});
    delete this;
};

function initialize () {
    bindControls();
    sendCommand('devices', {}, onDevices);

    //DEBUGGING PURPOSES
    sendCommand('tasks',{},function (tasks) {
	for (var task in tasks) {
	    sendCommand('clear task', {'task':tasks[task]});
	}
	new Acquisition('test','alpha','ai0');
    });    
}

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
		new Acquisition(name, device, channel);
	    }
	);
    });
};

function selectedDevice () {
    return $('#device > option:selected').prop('value');
};

function selectedChannel () {
    return $('#channel > option:selected').prop('value');
};

function selectedName() {
    return $('#name').prop('value');
};

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

function onDevices (devices) {
    $('#device').empty();
    $.each(devices,function (index,value) {
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

function onPhysicalChannels (channels) {
    $('#channel').empty();
    $.each(channels, function(index, value) {
	$('#channel').append(
	    $('<option>').prop('value',value).prop('label',value)
	);
    });
};
