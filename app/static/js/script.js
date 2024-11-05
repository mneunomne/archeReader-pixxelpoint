
const messageContainer = document.getElementById('characters')

const video_width = 800
const video_height = 600

const transition_duration = 4000

var map_height;

var map;
var isAnimating = false;

var borderSections = [];
var latestBorderSection = null;

// Array of overlay data extracted from XML
const overlayData = [
	{ name: 'carinarnica-0', bounds: { north: 45.9057128686006, south: 45.89194144932638, east: 13.61750134737098, west: 13.59769853902374 }},
	{ name: 'carinarnica-1', bounds: { north: 45.91451180583061, south: 45.90074038655639, east: 13.62402909011504, west: 13.6042262817678 }},
	{ name: 'carinarnica-2', bounds: { north: 45.92698187338779, south: 45.91321045411356, east: 13.63449571413881, west: 13.61469290579157 }},
	{ name: 'carinarnica-3', bounds: { north: 45.93840130626697, south: 45.92462988699274, east: 13.64312246615163, west: 13.62331965780439 }},
	{ name: 'carinarnica-4', bounds: { north: 45.94935526008752, south: 45.93558384081329, east: 13.64572055121937, west: 13.62591774287213 }},
	{ name: 'carinarnica-5', bounds: { north: 45.95951763586891, south: 45.94574621659469, east: 13.64376728003707, west: 13.62396447168983 }},
	{ name: 'carinarnica-6', bounds: { north: 45.96943020712954, south: 45.95565878785532, east: 13.64657156135182, west: 13.62676875300457 }},
	{ name: 'carinarnica-7', bounds: { north: 45.97760939709851, south: 45.96383797782428, east: 13.65012521215656, west: 13.63032240380932 }}
];


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
		zoom: 17,
		zoomControl: false,
		disableDefaultUI: true,
		//tilt: 0
	});

	// disable zoom control
	// Set satellite view
	//map.setMapTypeId('satellite');

	const imageBounds = {
		north:  45.976872,  // maxLat
		south:  45.900527,  // minLat
		east:  13.685776,   // maxLng
		west:  13.575996    // minLng
	};


	const overlay = new google.maps.GroundOverlay('img/nova_gorica-8_2023_blue.png', imageBounds);
	overlay.setMap(map);

	// Initialize Google Maps overlays
	overlayData.forEach(data => {
		const imageBounds = {
				north: data.bounds.north,
				south: data.bounds.south,
				east: data.bounds.east,
				west: data.bounds.west
		};

		const _overlay = new google.maps.GroundOverlay(`img/small/${data.name}.jpg`, imageBounds);
		_overlay.setMap(map);
	});

	// set map height
	//let map_height = 1920 - video_height
	console.log("map_height", window.innerHeight, map_height)
	setInterval(() => {
		document.getElementById('map').style=`width: ${window.innerWidth}px; height: ${map_height}px;`
	}, 100)

}

var curPointIndex = 0;

var numAttempts = 100;

var maxZoom = 20;
var minZoom = 15;

function setPathPoint(position, index, attempt) {
	var polyline = latestBorderSection.polyline;
	var pathCoordinates = latestBorderSection.pathCoordinates;
	attempt++;
	//const latLng = new google.maps.LatLng(position.lat, position.lon);
	var latstr = position.lat.toString();
	var lonstr = position.lon.toString();

	// map attempt from numAttempts to 0 from minZoom to maxZoom
	var ratio = (attempt) / numAttempts;
	var newZoom = minZoom + (maxZoom - minZoom) * ratio; 

	let scale = 100 / Math.pow(2, (attempt));
	// console.log("scale", scale)

	// make pos attempt/latstr random
	latstr = (position.lat + (Math.random()-0.5) * scale).toString();
	lonstr = (position.lon + (Math.random()-0.5) * scale).toString();

	var lat = parseFloat(latstr);
	var lon = parseFloat(lonstr);

	var latLng = new google.maps.LatLng(lat, lon);
	
	pathCoordinates[index] = latLng;

	// Add the new position to the pathCoordinates array
	//pathCoordinates[pathCoordinates.length] = latLng;
	//curPointIndex = pathCoordinates.length - 1;

	// Update the polyline path with the new coordinates
	polyline.setPath(pathCoordinates);

	//map.setZoom(newZoom);
	//map.setCenter(new google.maps.LatLng(position.lat, position.lon));

	// console.log("attempt", attempt);

	if (attempt < numAttempts) {
		setTimeout(() => {
			setPathPoint(position, index, attempt);
		}, 5000/numAttempts);
	}
}

function updateBorderLine(position) {
	smoothPanTo(position);
	setPathPoint(position, latestBorderSection.pathCoordinates.length, 0);
	return;
	const latLng = new google.maps.LatLng(position.lat, position.lon);

	// Add the new position to the pathCoordinates array
	pathCoordinates[pathCoordinates.length] = latLng;
	//curPointIndex = pathCoordinates.length;

	// Update the polyline path with the new coordinates
	latestPolyline.setPath(pathCoordinates);

	// if coordinates are bigger than 100 remove the first one
	if (pathCoordinates.length > 500) {
		pathCoordinates.shift();
	}

	// Smoothly pan the map to the new position
	//smoothPanTo(position);
}

function smoothPanTo(target) {
	if (isAnimating) return;

	const currentCenter = map.getCenter();
	const startLat = currentCenter.lat();
	const startLng = currentCenter.lng();
	const endLat = target.lat;
	const endLng = target.lon;
	const duration = 1000; // Duration of the animation in milliseconds
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

  map_height = window.innerHeight - h + 22; // 20 is to hide the google stuff

  document.getElementById('video').style=`width: ${w}px; height: ${h}px;`

  // document.getElementById('video2').style=`width: ${w}px; height: ${h2}px;`
	// document.getElementById('map').style=`width: ${w}px; height: ${h2}px;`
  
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
    if (event.data.includes("detection")) {
      var msg = event.data.split("detection-")[1]
      onSegmentData({data: msg})
    }
  };

	var key_index = 0;

  // Update the position of the map and the planetarium
  document.addEventListener('keyup', function (event) {
    if (event.key == 'i') {
      let s = border_strings[key_index]
			key_index++;
			if (key_index >= border_strings.length) {
				key_index = 0;
			}
      console.log("s", s)
      onSegmentData({data: s})
			return
    }
    if (event.key == 't') {
      let s = border_strings[Math.floor(Math.random() * border_strings.length)]
      console.log("s", s)
      onSegmentData({data: s})
			return
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

		let splitIndex = closest(20, getAllIndexes(string, "|"))
		string.replace("|", "1")
		string[splitIndex] = "|"
		console.log("fixed string", string)

		// get "|" char closest to the middle of the string
		var middle = Math.floor(string.length / 2);
		var index = string.indexOf('|', middle);
		if (index == -1) {
			index = string.indexOf('|');
		}


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

  // add socket events
	/*
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

		var isValid = validateSegment(data)

		if (isValid) {
			if (latestBorderSection == null) {
				initializeBorderSection(data)
			}
			console.log("borderSections", borderSections)
			updateBorderLine(data)
		} else {
			latestBorderSection = null
		}
    // t;ransitionPlanetarium(data, transition_duration)

		/*
    hideMessage()
    setTimeout(() => {
      displayMessage(string)
    }, transition_duration)
		*/
  }

	const initializeBorderSection = function (position) {
		const latLng = new google.maps.LatLng(position.lat, position.lon);

		var pathCoordinates = []; // Array to store the path coordinates
		pathCoordinates[0] = latLng;

		// Initialize the Polyline with an empty path
		var polyline = new google.maps.Polyline({
			path: pathCoordinates,
			geodesic: true,
			strokeColor: '#FF0000', // red #FF0000
			strokeOpacity: 1,
			strokeWeight: 8
		});
		
		// Add the polyline to the map
		polyline.setMap(map);

		var borderSection = {
			pathCoordinates,
			polyline
		}

		borderSections.push(borderSection);
		latestBorderSection = borderSection;
	}

	const validateSegment = function (data) {
		if (Math.random() < 0.1) {
			return false
		}
		if (data.lat == 0 || data.lon == 0) {
			return false
		} else {
			// check if .lat and .lon are valid numbers
			if (isNaN(data.lat) || isNaN(data.lon)) {
				return false
			}
			// check if they are valid coordinates
			if (data.lat > 90 || data.lat < -90 || data.lon > 180 || data.lon < -180) {
				return false
			}
		}
		return true
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

function getAllIndexes(arr, val) {
	var indexes = [], i = -1;
	while ((i = arr.indexOf(val, i+1)) != -1){
			indexes.push(i);
	}
	return indexes;
}

function closest (num, arr) {
	var curr = arr[0];
	var diff = Math.abs (num - curr);
	for (var val = 0; val < arr.length; val++) {
			var newdiff = Math.abs (num - arr[val]);
			if (newdiff < diff) {
					diff = newdiff;
					curr = arr[val];
			}
	}
	return curr;
}
