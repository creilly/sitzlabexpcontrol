chrome.app.runtime.onLaunched.addListener(function() {
  chrome.app.window.create(
      'daqclient.html',
      {
	  'width': 800,
	  'height': 800
      }
  );
});
