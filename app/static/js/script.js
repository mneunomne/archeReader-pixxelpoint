
const messageContainer = document.getElementById('characters')

const video_width = 800
const video_height = 600

const transition_duration = 4000

var map_height;

var map;
let isAnimating = false;
let pathCoordinates = []; // Array to store the path coordinates
let polyline; // Variable to hold the Polyline object


var border_strings = border.map((item) => {
	return (item.lat + '|' + item.lon).replace('.', '-')
})

var initial_pos = {lat: 45.95240469585346, lng: 13.634056757381002}


window.onload = function() {
  setTimeout(() => {
    if(!window.location.hash) {
        window.location = window.location + '#loaded';
        window.location.reload();
    }
  }, 5000)
}

const socket = new WebSocket(
  "ws://0.0.0.0:8025/arche-scriptures"
);

function initMap() {
	// Define the bounds using the given lat/lng values


	// Create a map centered within the bounds
	map = new google.maps.Map(document.getElementById("map"), {			
		center: initial_pos,
		zoom: 16,
		disableDefaultUI: true
	});

	// Initialize the Polyline with an empty path
	polyline = new google.maps.Polyline({
		path: pathCoordinates,
		geodesic: true,
		strokeColor: '#0029FF',
		strokeOpacity: 1,
		strokeWeight: 2.2
	});

	// Set satellite view
	map.setMapTypeId('satellite');

	// set map height
	let map_height = 1920 - video_height
	console.log("map_height", window.innerHeight, map_height)
	document.getElementById('map').style=`width: ${window.innerWidth}px; height: ${map_height}px;`

}

function updateBorderLine(position) {
	const latLng = new google.maps.LatLng(position.lat, position.lon);

	// Add the new position to the pathCoordinates array
	pathCoordinates.push(latLng);

	// Update the polyline path with the new coordinates
	polyline.setPath(pathCoordinates);

	// if coordinates are bigger than 100 remove the first one
	if (pathCoordinates.length > 500) {
		pathCoordinates.shift();
	}

	// Smoothly pan the map to the new position
	smoothPanTo(position);
}

function smoothPanTo(target) {
	if (isAnimating) return;

	const currentCenter = map.getCenter();
	const startLat = currentCenter.lat();
	const startLng = currentCenter.lng();
	const endLat = target.lat;
	const endLng = target.lon;
	const duration = Math.random() * 10000 + 1000; // Duration of the animation in milliseconds
	const frameRate = 24; // Frames per second
	const totalFrames = Math.round((duration / 1000) * frameRate);
	let currentFrame = 0;

	isAnimating = true;

	function animate() {
		currentFrame++;
		const progress = easeInOutQuad(currentFrame / totalFrames);
		const lat = startLat + (endLat - startLat) * progress;
		const lng = startLng + (endLng - startLng) * progress;
		map.setCenter(new google.maps.LatLng(lat, lng));

		if (currentFrame < totalFrames) {
			requestAnimationFrame(animate);
		} else {
			isAnimating = false;
		}
	}

	animate();
}

// Easing function for smooth animation
function easeInOutQuad(t) {
	return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
}

const resizeVideo = function () {
  var ratio = video_width / video_height

  let w = window.innerWidth
  let h = w/ratio
  let h2 = window.innerHeight - h

  map_height = window.innerHeight - h

  document.getElementById('video').style=`width: ${w}px; height: ${h}px;`
  document.getElementById('video2').style=`width: ${w}px; height: ${h2}px;`

	//document.getElementById('map').style=`width: ${w}px; height: ${h2}px;`
  
}

S(document).ready(function () {
  let w = window.innerWidth;
  let h = window.innerHeight;
  resizeVideo();
  initMap()

  socket.onmessage = (event) => {
    console.log("onmessage", event.data);
    if (event.data.includes("fail")) {
      return
    } 
    if (event.data.includes("detection-")) {
      var msg = event.data.split("detection-")[1]
      onSegmentData({data: msg})
    }
  };

  // Update the position of the map and the planetarium
  document.addEventListener('keyup', function (event) {
    if (event.key == 't') {
      let s = border_strings[Math.floor(Math.random() * border_strings.length)]
      console.log("s", s)
      onSegmentData({data: s})
    }
    // if key is number 0-9, send get request to server /on_segment/<segment_number>
    if (event.key >= '0' && event.key <= '9') {
      // send get request to server
      let segment_number = parseInt(event.key)

      //return onSegmentData({data: data[segment_number]})

      $.get("/on_segment/" + segment_number, function (data, status) {
        console.log("data", data)
        onSegmentData({data: data})
      });
    }
    n = undefined;
    // 10-19
    switch (event.key) {
      case 'q': n = 10; break;
      case 'w': n = 11; break;
      case 'e': n = 12; break;
      case 'r': n = 13; break;
      case 't': n = 14; break;
      case 'y': n = 15; break;
      case 'u': n = 16; break;
      case 'i': n = 17; break;
      case 'o': n = 18; break;
      case 'p': n = 19; break;
      default:
        break;
    }
    if (n !== undefined) {
      $.get("/on_segment/" + n, function (data, status) {
        console.log("data", data)
        onSegmentData({data: data})
      });
    }
  });

  window.addEventListener('resize', function (event) {
    console.log("resize")
    resizeVideo()
  })

  // shuffle string function
  String.prototype.shuffle = function () {
    var a = this.split(""), n = a.length;
    for(var i = n - 1; i > 0; i--) {
        var j = Math.floor(Math.random() * (i + 1));
        var tmp = a[i];
        a[i] = a[j];
        a[j] = tmp;
    }
    return a.join("");
  }

	// decode function
  var decode = function (string) {
    var data = string.split("|").map((item) => {
      item = item.replace(/^(X+)/g, '')
      item = item.replace('-', '.')
      console.log("item", item)
      return parseFloat(item)
    })
    return {
      lat: validateLocation(data[0]),
      lon: validateLocation(data[1])
    }
  }

  var validateLocation = function (num){
    if (isNaN(num) || num == undefined || num == null) {
      return 0
    }
    let s = num + ''
    if (num > 90) {
      num = parseFloat(s[0] + '.' + s.substring(1, s.length))
    }
    if (num < -90) {
      num = parseFloat(s.substring(0, 2) + '.' + s.substring(2, s.length))
    }
    if (isNaN(num) || num == undefined || num == null) {
      return 0
    }
    return num
  }

/*
  // add socket events
  socket.on('connect', function () {
    console.log('connected');
  });

  socket.on('disconnect', function () {
    console.log('disconnected');
  });

  // on message 'detection_data'
  socket.on('detection_data', function (msg) {
    console.log('detection_data', msg);
    onSegmentData(msg)
  });
  */

  const onSegmentData = function (msg) {
    console.log('detection_data', msg);
    var string = msg.data//.replace(/X/g, '')
    console.log('string', string);
    var data = decode(string)
    console.log("decode data", data)

		updateBorderLine(data)

    // transitionPlanetarium(data, transition_duration)

    hideMessage()
    setTimeout(() => {
      displayMessage(string)
    }, transition_duration)
  }

  const displayMessage = function (msg) {
    msg.split('').map((char, index) => {
      if (char == '.') char = '-'
      const img = document.createElement('img')
      img.src='templates/' + char + '.svg'
      img.style = `transition-delay: ${index * 0.01}s;`
      messageContainer.appendChild(img)
      if (char == '|') {
        const br = document.createElement('br')
        messageContainer.appendChild(br) 
      }
    })
    setTimeout(() => {
      // hideMessage()
      messageContainer.className = 'show'
    }, 100)
  }

  const hideMessage = function () {
    messageContainer.className = ''
    setTimeout(() => {
      messageContainer.innerHTML = ''
    }, 1500)
  }
  /*
  // clear message
  socket.on('clear', function (msg) {
    console.log('clear', msg);
  });
  */
});
