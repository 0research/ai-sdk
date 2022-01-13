if (!window.dash_clientside) {
    window.dash_clientside = {};
}

window.dash_clientside.clientside = {
    get_cytoscape_position: function(n_clicks) {
		if (n_clicks == 0) {
			console.log('n_clicks: ', n_clicks)
			return []
		}
		console.log('Nodes:', cy.nodes().jsons());
		nodes = cy.nodes().jsons()
		var node_position_list = [];
		for (let i = 0; i < nodes.length; i++) {
			node_position_list.push({
				'id': nodes[i]['data']['id'],
				'position': nodes[i]['position'],
				'type': nodes[i]['data']['type']
			})
		}
		 
		return node_position_list
    }


}