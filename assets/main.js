if (!window.dash_clientside) {
    window.dash_clientside = {};
}




window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        get_cytoscape_position: function(n_intervals, position_store) {
			if (position_store == JSON.stringify(cy.nodes().jsons())) {
				return ''
			} else {
				return cy.nodes().jsons()
			}
		}

		// initialize_cytoscape: function(pathname) {
		// 	console.log("BBBBBBBBBBBBBBBBB")
		// 	console.log(cy)
		// 	return ''
		// },
    }
});





// import typesense from "typesense"
// const typesense = require('typesense')



// window.addEventListener("load", function () {
	
// 	console.log('START 0')
// 	console.log(cy)
// 	// let socket = new WebSocket('wss://websocket-echo.glitch.me');

// 	// socket.onopen = function(e) {
// 	// 	alert("Sending to server");
// 	// 	socket.send("My name is John");
// 	// 	alert("Sending to server22222");
// 	// 	socket.send("My name is John2222");
// 	// };
	
// 	/* Cytoscape Start */
// 	var input_store = document.getElementById("data_lineage-cytoscape_position")
// 	var cy2 = document.getElementById("data_lineage-cytoscape")
// 	console.log(cy2)
// 	console.log(cy)
// 	cy.on('position', function(event) {
// 		// Send socket data
// 		console.log("POS")
// 		input_store.value = JSON.stringify(cy.nodes().jsons())
// 	})

// 	/* Cytoscape End */
// });


// window.addEventListener("DOMContentLoaded", function () {
// 	console.log('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
// 	console.log(cy)
// });