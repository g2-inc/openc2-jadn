const toggleClick = e => {
    var btn = $(e.target)
	var target = $(btn.data("target"))
	btn.text((target.hasClass('show') ? 'Show' : 'Hide') + ' API')
}

const under_escape = val => val.replace(/\./g, '_')

const dynamic_sort = (key, order='asc') => {
	return function(a, b) {
    	if(!a.hasOwnProperty(key) || !b.hasOwnProperty(key)) {
      		// property doesn't exist on either object
      		return 0;
    	}

    	const varA = (typeof a[key] === 'string') ? a[key].toUpperCase() : a[key];
    	const varB = (typeof b[key] === 'string') ? b[key].toUpperCase() : b[key];
		let comparison = 0;
    	if (varA > varB) {
      		comparison = 1;
    	} else if (varA < varB) {
      		comparison = -1;
    	}
    return (
      (order == 'desc') ? (comparison * -1) : comparison
    );
  };
}

const pkg_format = pkg => {
	if (pkg.hasOwnProperty('body')) {
		var tmp_body = '<div id="' + under_escape(pkg.header) + '-api" class="row collapse px-2">'
		pkg.header = $.templates.toggle_template.render({header: pkg.header})
				
		if (pkg.body.hasOwnProperty('package')) {
			var keys = Object.keys(pkg.body.package).sort()
			$.each(keys, (i, name) => {	
				var data = pkg.body.package[name]
				data.header = name
				tmp_body += pkg_format(data)
			})
		}
		
		if (pkg.body.hasOwnProperty('enum')) {
			var keys = Object.keys(pkg.body.enum).sort()
			$.each(keys, (i, name) => {
				val = pkg.body.enum[name]
				val.header = name
				val.body = ''
				if (val.hasOwnProperty('constructor')) {
					val.body += $.templates.constructor_template.render(val.constructor)
				}
				
				if (val.hasOwnProperty('enum')) {
					val.body += $.templates.enum_template.render({enum: val.enum})
				}
							
				if (val.hasOwnProperty('function')) {
					val.body += $.templates.function_template.render({function: val.function})
				}
				tmp_body += $.templates.card_template.render(val)
			})				
		}
		
		if (pkg.body.hasOwnProperty('class')) {
			var classes = pkg.body.class.sort(dynamic_sort('header'))
			$.each(classes, (i, cls) => {
				cls.body = ''
				cls.header = name
				if (cls.hasOwnProperty('constructor')) {
					cls.body += $.templates.constructor_template.render(cls.constructor)
				}
				
				if (cls.hasOwnProperty('enum')) {
					cls.body += $.templates.enum_template.render({enum: cls.enum})
				}
							
				if (cls.hasOwnProperty('function')) {
					cls.body += $.templates.function_template.render({function: cls.function})
				}
				tmp_body += $.templates.card_template.render(cls)
			})		
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
