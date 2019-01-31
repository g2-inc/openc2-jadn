<script id="card-template" type="text/x-jsrender">
	<div class="row card bg-light mb-3">
		<h3 class="card-header">{{ header }}</h3>
		<div class="card-body">
			<h4 class="card-title">{{ card-title }}</h4>
			{{ if card-text }}
				{{ props card-text }}
    				<p class="card-text">{{ :prop }}</p>
				{{ /props }}
  			{{/if}}
			{{ if card-body }}
    			{{ card-body }}
  			{{/if}}
			
		</div>
	</div>
</script>