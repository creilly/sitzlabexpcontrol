var counter = 0;
var xScale, yScale, svg;
var RADIUS = 3.0;
function plot (data) {

    if (counter == 0) {

	var WIDTH = 400.0;
	var HEIGHT = 400.0;
	var PADDING = .1;
	var Y_AXIS_PADDING = 0.0;
	var X_AXIS_PADDING = 0.0;

	svg = d3.select('svg');

	svg.attr('width',WIDTH).attr('height',HEIGHT);

	var transpose = d3.transpose(data);
	
	xScale = d3.scale.linear()
	    .domain(d3.extent(transpose[0]))
	    .range([WIDTH * PADDING,WIDTH * ( 1.0 -PADDING )]);

	yScale = d3.scale.linear()
	    .domain(d3.extent(transpose[1]))
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

    }

    svg.selectAll('circle').remove();

    svg.selectAll('circle')
	.data(data)
	.enter()
	.append('circle')
	.attr('cx',function(d){return xScale(d[0])})
	.attr('cy',function(d){return yScale(d[1])})
	.attr('r',RADIUS);

    counter++;
}

function gaussian(n, mean, spread) {

    var ran = Math.random;

    var data = [];

    for (var i = 0; i < n; i++) {
	var x = ((ran() + ran() + ran()) / 3 - .5 ) * spread + mean;
	var y = ((ran() + ran() + ran()) / 3 - .5 ) * spread + mean;
	data[i] = [x,y];
    }

    return data;
};

var nPoints = 1000;
var mean = 0.0;
var spread = 4.0;

setInterval(function() {plot(gaussian(nPoints,mean + .001 * counter,spread))},40);

