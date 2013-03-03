function terminate () {
    drawBox();
}
var W = 200;
var H = 80;
var paper;

function xp (x) {return x * W;}
function yp (y) {return (1-y)* H;}
function xw (x) {return x * W;}
function yw (y) {return y * H;}
function rr (r) {return W * r;}

function drawBox () {
    RIGHT = true;
    LEFT = false;
    function cr (x, dx, dy) {
	return paper.rect(xp(x),yp(.5 + dy / 2),xw(dx), yw(dy));
    };
    function cb (x,align) {
	var set = paper.set();
	var bar = cr(x,.01,.7).attr('fill','black').attr('stroke','none').insertAfter(bbox);
	var bang = paper
	    .text(xp(x + .02 * (align ? 1 : -1)),yp(.9),'!')
	    .attr('font-size',rr(.05))
	    .attr('text-align',align ? 'start':'end');
	set.push([bar,bang]);
	set.hover(
	    function(){
		bang.attr('font-weight','bold').tooltip('show');
		bar.attr('stroke','purple');
	    },
	    function(){
		bang.attr('font-weight','normal');
		bar.attr('stroke','none');
	    }
	);	
	$(bang.node).css('cursor','default');
	return bang;
    }
    paper = Raphael($('#sensors')[0],xw(1),yw(1));
    var bbox = cr(.1,.8,.5).attr('stroke-width',rr(.02));
    var meter = cr(.1,.4,.5).attr('fill','blue').insertBefore(bbox);
    var bang = cb(.3,RIGHT);
}
