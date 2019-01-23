const toggleClick = e => {
    var btn = $(e.target)
	var target = $(btn.data("target"))
	btn.text((target.hasClass('show') ? 'Show' : 'Hide') + ' API')
}

const under_escape = val => val.replace(/\./g, '_')

const pkg_format = pkg => {
	if (pkg.hasOwnProperty('body')) {
		var tmp_body = '<div id="' + under_escape(pkg.header) + '-api" class="row collapse px-2">'
		pkg.header = $.templates.toggle_template.render({header: pkg.header})
				
		if (pkg.body.hasOwnProperty('package')) {
			for (var name in pkg.body.package) {
				var data = pkg.body.package[name]
				data.header = name
				tmp_body += pkg_format(data)
			}
		}
		
		if (pkg.body.hasOwnProperty('enum')) {
			for (var i in pkg.body.enum) {
				var tmp = pkg.body.enum[i]
				tmp.body = ''
				if (tmp.hasOwnProperty('constructor')) {
					tmp.body += $.templates.constructor_template.render(tmp.constructor)
				}
				
				if (tmp.hasOwnProperty('enum')) {
					tmp.body += $.templates.enum_template.render({enum: tmp.enum})
				}
							
				if (tmp.hasOwnProperty('function')) {
					tmp.body += $.templates.function_template.render({function: tmp.function})
				}
				tmp_body += $.templates.card_template.render(tmp)
			}					
		}
		
		if (pkg.body.hasOwnProperty('class')) {
			for (var i in pkg.body.class) {
				var tmp = pkg.body.class[i]
				tmp.body = ''
				if (tmp.hasOwnProperty('constructor')) {
					tmp.body += $.templates.constructor_template.render(tmp.constructor)
				}
				
				if (tmp.hasOwnProperty('enum')) {
					tmp.body += $.templates.enum_template.render({enum: tmp.enum})
				}
							
				if (tmp.hasOwnProperty('function')) {
					tmp.body += $.templates.function_template.render({function: tmp.function})
				}
				tmp_body += $.templates.card_template.render(tmp)
			}					
		}
			
		if (pkg.body.hasOwnProperty('function')) {
			tmp_body += $.templates.function_template.render({function: pkg.body.function})
		}
		pkg.body = tmp_body + '</div>'
	}
	
	return $.templates.card_template.render(pkg)
}

$(document).ready(() => {
	//$("#templates").load("/js/templates.html", () => {
		$.views.helpers({
			under_escape: under_escape
		})
		
		$.templates({
			card_template: "#card_template",
			toggle_template: "#toggle_template",
			constructor_template: "#constructor_template",
			enum_template: "#enum_template",
			function_template: "#function_template",
		})
			
		for (var pkg in jadn_api) {
			var data = jadn_api[pkg]
			data.header = pkg			
			$("#api").append(pkg_format(data))
		}
		
		$('button[data-toggle="collapse"]').each((i, btn) => {
			$(btn).click(toggleClick)
		})
	//})	
})