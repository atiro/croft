from pathlib import Path
import sqlite_utils
import csv
import pkg_resources

class Quarto:

    def __init__(self, keep_nav_names=False, config=None):
        self.views = {}
        self._keep_nav_names = keep_nav_names
        self._config = config

    def add_views(self, datasource):
        active_view = None

        for view in datasource.views:
            view_config = self._config["views"][view]

            if view == "table":
                active_view = Table(datasource = datasource, primitives=view_config["primitives"], slug=view_config["slug"], title=view_config["title"], primary=view_config["primary"], output_list=view_config["output_list"], output_map=view_config["output_map"], options=view_config["options"])
            elif view == "gallery":
                active_view = Gallery(datasource = datasource, primitives=view_config["primitives"], slug=view_config["slug"], title=view_config["title"], primary=view_config["primary"], output_map=view_config["output_map"], options=view_config["options"])
            elif view == "map":
                active_view = Map(datasource = datasource, primitives=view_config["primitives"], slug=view_config["slug"], title=view_config["title"], primary=view_config["primary"], output_map=view_config["output_map"], options=view_config["options"])

            if active_view:
              self.add_view(active_view)
            else:
              print(f"Unknown view type {view} referenced, ignoring")

    def add_view(self, view = None):
        # TODO - retrueve URL and name
        title = view.title
        view_type = view.__class__.__name__.lower()
        if view_type not in self.views:
            self.views[view_type] = {}

        self.views[view_type][title] = {}
        self.views[view_type][title]["active_view"] = view
        # TODO do we need this now we handle this ourselves ?
        self.views[view_type][title]['slug'] = view.slug
        self.views[view_type][title]['title'] = view.title
        self.views[view_type][title]['primary'] = view.primary

    def write(self, dir_base = None):

      # Construct the config file
      # TODO some of this is specific to views (e.g. resources) so should
      # only be written if those views are there

      project_config = """
project:
  type: website
  resources:
    - pwa.js
    - sw.js
    - webworker.js
"""
      website_config = f"""
website:
  title: {self._config['site']['name']}
  navbar:
    background: primary
    left:
"""

      format_config = """
format:
  html:
    theme: lux
    css: 
      - leaflet.css
      - MarkerCluster.css
      - MarkerCluster.Default.css
"""
     # TODO - should only add leaflet if map view added

     # Add the views

      for view_type in self.views:

        # First write out the views data files

        
        # Now add to nav menus

        # If more than one of this type, only the primary is written here, the other(s)
        # go in side nav switcher. We also use either the view type name or user set name
       primary_item = ""
       submenu_items = ""
       for view in self.views[view_type]:
         self.views[view_type][view]['active_view'].write(dir_base)

         if self.views[view_type][view]['primary']:
           if len(self.views[view_type]) > 1:
             primary_item = f"""
        - text: {self.views[view_type][view]['title'] if self._keep_nav_names else view_type.capitalize()}
          href: {view_type}/{self.views[view_type][view]['slug']}/index.qmd"""
           else:
             primary_item = f"""
      - text: {self.views[view_type][view]['title'] if self._keep_nav_names else view_type.capitalize()}
        href: {view_type}/{self.views[view_type][view]['slug']}/index.qmd"""
         else:
           submenu_items += f"""
        - text: {self.views[view_type][view]['title']}
          href: {view_type}/{self.views[view_type][view]['slug']}/index.qmd"""
          
       print(f"{primary_item}")
       if len(submenu_items) > 0:
          view_item = f"\n      - text: {view_type.capitalize()}\n        menu:"
          website_config += f"{view_item}{primary_item}{submenu_items}"
       else:
          website_config += primary_item

      # Write out the intro page

      with open(f"{dir_base}/content/mysite/index.qmd", "w") as homepage_file:
        homepage_file.write("---\n")
        homepage_file.write(f"title: \"{self._config['site']['title']}\"\n")
        homepage_file.write("---\n")
        homepage_file.write(self._config['site']['intro_long'])

      with open(f"{dir_base}/content/mysite/_quarto.yml", "w") as quarto_file:
        quarto_file.write(project_config + website_config + format_config)

class View:

    def __init__(self, datasource = None, primitives = [], slug = None, title = None, primary= False, output_map = None, output_list = None, options = None):
        self._primitives = primitives
        self._slug = slug
        self._title = title
        self._primary = primary
        # Field settings should be done in some more comprhensive way for all the 
        # available options for each view, perhaps a dict ?
        self._output_map = output_map
        self._output_list = output_list
        self._options = options
        self.statements = datasource.statements
        self.data_files = datasource.data_files

    @property
    def title(self):
        return self._title

    @property
    def slug(self):
        return self._slug

    @property
    def primitives(self):
        return self._primitives

    @property
    def link(self):
        return self._link

    @property
    def primary(self):
        return self._primary

    def output_map(self, statement = None, name = ""):
        if name and name in self._output_map:
          prim, field = self._output_map[name].split("::")
          print(f"Mapping  {name} to {prim} and {field}")
          return statement[prim].get_primary_field(field)
        else:
          return None

    def output_list(self, statement = None, name = ""):
        prim, field = name.split("::")
        print(f"List retrieving {name} to {prim} and {field}")
        return statement[prim].get_primary_field(field)

class Gallery(View):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def write(self, dir_base = None):

       if self.slug is None:
         public_name = self.primitive[0].lower()
       else:
         public_name = self.slug

       Path(f"{dir_base}/content/mysite/gallery/{public_name}").mkdir(parents=True, exist_ok=True)

       print(f"Writing gallery out for primitives {self.primitives}")

       for link_item in self.statements:
         for gall_item in self.statements[link_item]:

            print(f"[Gallery] [Link ID] - {gall_item}")

            item_data = self.statements[link_item][gall_item]
            print(f"[Gallery] [Item Data] - {item_data}")
            filename = item_data["_filename_"]
            fields = item_data[self.primitives[0]].get_primary_fields()
            if len(fields) == 0:
              # If this item doesn't have anything set for the primitive wanted for this view, skip
              print(f"No values set for {gall_item}, skipping")
              continue

            with open(f"{dir_base}/content/mysite/gallery/{public_name}/{filename}.qmd", "w") as hugo_file:
                hugo_file.write("---\n")

                print(f"[Gallery] [self] - {self}")
                title_field = self.output_map(item_data, name="Title")
                if title_field != None:
                  hugo_file.write(f"title: \"{title_field}\"\n")

                name_field = self.output_map(item_data, name="Subtitle")
                hugo_file.write(f"subtitle: \"{name_field}\"\n")
                desc_field = self.output_map(item_data, name="Description")
                hugo_file.write(f"description: \"{desc_field}\"\n")
                img_field = self.output_map(item_data, name="Image")
                if img_field != "":
                 hugo_file.write(f"image: \"{img_field}/full/300,/0/default.jpg\"\n")
                 hugo_file.write(f"thumbnail: \"{img_field}/full/200,/0/default.jpg\"\n")
                author_field = self.output_map(item_data, name="Author")
                if author_field != None:
                  hugo_file.write(f"author: \"{author_field}\"\n")
                # TODO this needs to be a config option as a image fallback

#                hugo_file.write("date: 2021-06-26T17:50:41+01:00\n")
                hugo_file.write("draft: false\n")
                hugo_file.write("title-block-banner: false\n")
                hugo_file.write(f"format:\n    html:\n        template-partials:\n         - title-block.html\n")
                hugo_file.write("---\n")

                hugo_file.write(f"## {title_field}\n")
                hugo_file.write(f"### {name_field}\n")
                hugo_file.write(f"{desc_field}\n\n")
                if img_field != None:
#                  hugo_file.write(f"## Image\n")
                  hugo_file.write("::: {.column-margin}\n")
                  hugo_file.write(f"<img src=\"{img_field}/full/400,/0/default.jpg\">\n\n")
                  hugo_file.write(f":::\n\n")
                url_field = self.output_map(item_data, "URL")
                if url_field != None:
                  hugo_file.write(f"## Collection Website\n")
                  hugo_file.write(f"<a href=\"{url_field}\"/>{title_field}</a> ({author_field})\n")

            # TODO how is this made a config option in croft ?
            with open(f"{dir_base}/content/mysite/gallery/{public_name}/title-block.html", "w") as hugo_file:
                pass

            gallery_ejs = """
```{=html}

<div class="list grid" style="column-gap: 10px;">

<% for (const tile of items) { %>
  <div class="card border-2 rounded-3 g-col-12 g-col-sm-6 g-col-md-4 mb-2" <%= metadataAttrs(tile) %>>
   <div class="card-body">
    <div class="card-header py-1 px-2 border-bottom border-1 ">
        <small class="card-title"><%= tile.subtitle %></small>
      <small class="inline-block text-right">
        <a href="<%- tile.path %>" class="listing-title"><%= tile.title %></a>
      </small>
    </div>
    <% if (tile.image) { %>
      <a href="<%- tile.path %>">
        <img src="<%- tile.thumbnail %>" alt="<%- tile.description %>" class="card-img-top"/>
    </a>
    <% } else { %>
        <span class="text-muted">No IIIF Image available yet</span>
   <% } %>
    <% if (tile.author ) { %>
      </div>
      <div class="card-footer">
           <span class="text-center"> <%- tile.author %></span>
   <% } %>
      </div>
  </div>
<% } %>
</div>

```
"""
            with open(f"{dir_base}/content/mysite/gallery/{public_name}/gallery.ejs", "w") as resource_file:
                resource_file.write(gallery_ejs)

            with open(f"{dir_base}/content/mysite/gallery/{public_name}/index.qmd", "w") as hugo_file:
                hugo_file.write("---\n")
                hugo_file.write(f"title: \"{self._title}\"\n")
                hugo_file.write("listing:\n")
                hugo_file.write("  filter-ui: true\n")
                hugo_file.write("  type: grid\n")
                hugo_file.write("  grid-columns: 4\n")
                hugo_file.write("  page-size: 100\n")
                hugo_file.write("  template: gallery.ejs\n")
                hugo_file.write("  fields: [title,subtitle]\n")
                hugo_file.write("  sort: \"subtitle\"\n")
                hugo_file.write("---\n")
                # TODO this needs to be configured from config settings

class Table(View):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def write(self, dir_base = None):

        if self.slug is None:
          public_name = self.primitive.lower()
        else:
          public_name = self.slug

        Path(f"{dir_base}/content/mysite/table/{public_name}").mkdir(parents=True, exist_ok=True)

        for link_item in self.statements:
          for gall_item in self.statements[link_item]:
            item_data = self.statements[link_item][gall_item]
            print(f"[Table] [Item Data] - {item_data}")
            filename = item_data["_filename_"]
            #if 'Name' not in primitive_fields:
               # Nothing set for this, ignore (e.g. has Actor values but not Event values)
            #   continue
           # TODO this should be prevented earlier (wrong primitives being passed
           # TODO the choice fif which primary provides which fields should be in the config
           # if 'Description' not in link_fields:
               # Nothing set for this, ignore (e.g. has Actor values but not Event values)
           #    print("No description set")
           #    continue

            print(item_data)
            title_field = self.output_map(item_data, name="Title")
            name_field = self.output_map(item_data, name="Subtitle")
            desc_field = self.output_map(item_data, name="Description")
            img_field = self.output_map(item_data, name="Image")
            url_field = self.output_map(item_data, "URL")
            author_field = self.output_map(item_data, "Author")

            filename = item_data["_filename_"]

            with open(f"{dir_base}/content/mysite/table/{public_name}/{filename}.qmd", "w") as hugo_file:
              hugo_file.write("---\n")

              for column in self._output_list:

                col_field = self.output_list(item_data, name=column[1])
                hugo_file.write(f"{column[0].lower()}: \"{col_field}\"\n")

#                name_field = self.output_map(item_data, name="Title")
#                hugo_file.write(f"title: \"{name_field}\"\n")
                # TODO how do we know this is correct ? I think is a config setting need to pickup
                # This should all be configured, diff primitives use diff fields
#                author_field = self.output_map(item_data, name="Author")
#                if author_field != None: 
#                  hugo_file.write(f"author: \"{author_field}\"\n")

#                year_field = self.output_map(item_data, name="Year")
#                if author_field != None: 
#                  hugo_file.write(f"year: \"{year_field}\"\n")

              hugo_file.write("draft: false\n")
              hugo_file.write(f"type: {public_name}\n")
              hugo_file.write("---\n")
              hugo_file.write(f"## {title_field}\n")
              hugo_file.write(f"### {name_field}\n")
              hugo_file.write(f"{desc_field}\n\n")
              if img_field != None:
                hugo_file.write("::: {.column-margin}\n")
                hugo_file.write(f"<img src=\"{img_field}/full/400,/0/default.jpg\">\n\n")
                hugo_file.write(f":::\n\n")
              if url_field != None:
                hugo_file.write(f"## Collection Website\n")
                hugo_file.write(f"<a href=\"{url_field}\"/>{title_field}</a> ({author_field})\n")

            # Need to map from our fields to the known Quarto fields (date, author, title..) based on
            # the config file settings

            with open(f"{dir_base}/content/mysite/table/{public_name}/index.qmd", "w") as hugo_file:
                hugo_file.write("---\n")
                hugo_file.write(f"title: \"{self._title}\"\n")
                hugo_file.write("listing:\n")
                hugo_file.write("  type: table\n")
                hugo_file.write("  table-striped: true\n")
                # TODO this should be coming from config
                hugo_file.write("  field-display-names:\n")
                for col in self._output_list:
                  hugo_file.write(f"    {col[0].lower()}: \"{col[2]}\"\n")

                col_names = ",".join([col[0].lower() for col in self._output_list])
                hugo_file.write(f"  fields: [{col_names}]\n")
                hugo_file.write(f"  sort-ui: [{col_names}]\n")
                if 'sort' in self._options:
                  hugo_file.write(f"  sort:\n")
                  for sort_col in self._options["sort"]:
                    hugo_file.write(f"    - \"{sort_col.lower()}\"\n")
                hugo_file.write(f"  sort-ui: [{col_names}]\n")
                hugo_file.write("---\n")


class Map(View):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def write(self, dir_base = None):
        link_fields = None

        if self.slug is None:
          public_name = self.primitive.lower()
        else:
          public_name = self.slug

        Path(f"{dir_base}/content/mysite/map/{public_name}").mkdir(parents=True, exist_ok=True)

        for link_item in self.statements:
          for map_item in self.statements[link_item]:
            item_data = self.statements[link_item][map_item]
            print(f"[Map] [Item Data] {map_item} - {item_data}")
            filename = item_data["_filename_"]
            fields = item_data[self.primitives[0]].get_primary_fields()
            if len(fields) == 0:
              print(f"No values set for {gall_item}, skipping")
              continue

#            if 'Name' not in primitive_fields:
               # Nothing set for this, ignore (e.g. has Actor values but not Event values)
               # TODO try link primitive fields
               # TODO maybe this isn't needed for map, test is location field below?
#               continue

            print(self.primitives[0])
            print(item_data[self.primitives[0]].get_primary_fields())
            if self.output_map(item_data, name='Location/Lat') == None:
               # Nothing set for this, ignore (e.g. has Actor values but not Event values)
               # TODO try link primitive fields
               continue

            filename = item_data["_filename_"]

            with open(f"{dir_base}/content/mysite/map/{public_name}/{filename}.qmd", "w") as hugo_file:
                hugo_file.write("---\n")

                name_field = self.output_map(item_data, name="Title")
                hugo_file.write(f"title: \"{name_field}\"\n")
                lat_field = self.output_map(item_data, name="Location/Lat")
                hugo_file.write(f"lat: \"{lat_field}\"\n")
                lon_field = self.output_map(item_data, name="Location/Lon")
                hugo_file.write(f"lon: \"{lon_field}\"\n")
                # XX how do we know this is correct ? I think is a config setting need to pickup
                author_field = self.output_map(item_data, name="Author")
                hugo_file.write(f"author: {author_field}\"\n")
                # TODO should this always be here ?
                desc_field = self.output_map(item_data, name="Description")
                hugo_file.write(f"description: \"{desc_field}\"\n")

                hugo_file.write("date: 2021-06-26T17:50:41+01:00\n")
                hugo_file.write("draft: false\n")
                hugo_file.write(f"type: {public_name}\n")
                hugo_file.write("---\n")


                map_ejs = """
```{=html}
<script src="https://unpkg.com/leaflet@1.8.0/dist/leaflet.js" integrity="sha512-BB3hKbKWOc9Ez/TAwyWxNXeoV9c1v6FIeYiBieIWkpLjauysF18NzgR1MBNBXf8/KABdlkX68nAhlwcDFLGPCQ==" crossorigin=""></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/leaflet.markercluster.js" integrity="sha512-OFs3W4DIZ5ZkrDhBFtsCP6JXtMEDGmhl0QPlmWYBJay40TT1n3gt2Xuw8Pf/iezgW9CdabjkNChRqozl/YADmg==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>

<div id="map" style="width: 90%; height: 800px;"></div>
<script>

	var map = L.map('map').setView([53.8167, -3.0370], 6);

	var tiles = L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw', {
		maxZoom: 18,
		attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, ' +
			'Imagery © <a href="https://www.mapbox.com/">Mapbox</a>'
,
		id: 'mapbox/streets-v11',
		tileSize: 512,
		zoomOffset: -1
	}).addTo(map);

        var markers = L.markerClusterGroup();
<% for (const item of items) { %>
    <% if (item.title.length > 0 ) { %>
	  markers.addLayer(L.marker([<%= item.lat %>, <%= item.lon %>]).bindPopup("<%= String(item.title) %>" + "(<%= String(item.author) %>"));
    <% } else { %>
	  markers.addLayer(L.marker([<%= item.lat %>, <%= item.lon %>]).bindPopup(""));
    <% } %>
<% } %>

      map.addLayer(markers);

</script>
```
"""

            with open(f"{dir_base}/content/mysite/map/{public_name}/map.ejs", "w") as resource_file:
                resource_file.write(map_ejs)

            resource_leaflet_css = """
.marker-cluster-small {
	background-color: rgba(181, 226, 140, 0.6);
	}
.marker-cluster-small div {
	background-color: rgba(110, 204, 57, 0.6);
	}

.marker-cluster-medium {
	background-color: rgba(241, 211, 87, 0.6);
	}
.marker-cluster-medium div {
	background-color: rgba(240, 194, 12, 0.6);
	}

.marker-cluster-large {
	background-color: rgba(253, 156, 115, 0.6);
	}
.marker-cluster-large div {
	background-color: rgba(241, 128, 23, 0.6);
	}

	/* IE 6-8 fallback colors */
.leaflet-oldie .marker-cluster-small {
	background-color: rgb(181, 226, 140);
	}
.leaflet-oldie .marker-cluster-small div {
	background-color: rgb(110, 204, 57);
	}

.leaflet-oldie .marker-cluster-medium {
	background-color: rgb(241, 211, 87);
	}
.leaflet-oldie .marker-cluster-medium div {
	background-color: rgb(240, 194, 12);
	}

.leaflet-oldie .marker-cluster-large {
	background-color: rgb(253, 156, 115);
	}
.leaflet-oldie .marker-cluster-large div {
	background-color: rgb(241, 128, 23);
}

.marker-cluster {
	background-clip: padding-box;
	border-radius: 20px;
	}
.marker-cluster div {
	width: 30px;
	height: 30px;
	margin-left: 5px;
	margin-top: 5px;

	text-align: center;
	border-radius: 15px;
	font: 12px "Helvetica Neue", Arial, Helvetica, sans-serif;
	}
.marker-cluster span {
	line-height: 30px;
	}
"""

            with open(f"{dir_base}/content/mysite/MarkerCluster.Default.css", "w") as resource_file:
                resource_file.write(resource_leaflet_css)

            resource_cluster_css = """
.leaflet-cluster-anim .leaflet-marker-icon, .leaflet-cluster-anim .leaflet-marker-shadow {
	-webkit-transition: -webkit-transform 0.3s ease-out, opacity 0.3s ease-in;
	-moz-transition: -moz-transform 0.3s ease-out, opacity 0.3s ease-in;
	-o-transition: -o-transform 0.3s ease-out, opacity 0.3s ease-in;
	transition: transform 0.3s ease-out, opacity 0.3s ease-in;
}

.leaflet-cluster-spider-leg {
	/* stroke-dashoffset (duration and function) should match with leaflet-marker-icon transform in order to track it exactly */
	-webkit-transition: -webkit-stroke-dashoffset 0.3s ease-out, -webkit-stroke-opacity 0.3s ease-in;
	-moz-transition: -moz-stroke-dashoffset 0.3s ease-out, -moz-stroke-opacity 0.3s ease-in;
	-o-transition: -o-stroke-dashoffset 0.3s ease-out, -o-stroke-opacity 0.3s ease-in;
	transition: stroke-dashoffset 0.3s ease-out, stroke-opacity 0.3s ease-in;
}
"""
           
            with open(f"{dir_base}/content/mysite/MarkerCluster.css", "w") as resource_file:
                resource_file.write(resource_cluster_css)

            # Obviously this is terrible. Need some way to pass resource files into
            # pip package, then copy them to a fixed location when installed so can
            # just copy into place

            resource_leaflet_css = """
/* required styles */

.leaflet-pane,
.leaflet-tile,
.leaflet-marker-icon,
.leaflet-marker-shadow,
.leaflet-tile-container,
.leaflet-pane > svg,
.leaflet-pane > canvas,
.leaflet-zoom-box,
.leaflet-image-layer,
.leaflet-layer {
	position: absolute;
	left: 0;
	top: 0;
	}
.leaflet-container {
	overflow: hidden;
	}
.leaflet-tile,
.leaflet-marker-icon,
.leaflet-marker-shadow {
	-webkit-user-select: none;
	   -moz-user-select: none;
	        user-select: none;
	  -webkit-user-drag: none;
	}
/* Prevents IE11 from highlighting tiles in blue */
.leaflet-tile::selection {
	background: transparent;
}
/* Safari renders non-retina tile on retina better with this, but Chrome is worse */
.leaflet-safari .leaflet-tile {
	image-rendering: -webkit-optimize-contrast;
	}
/* hack that prevents hw layers "stretching" when loading new tiles */
.leaflet-safari .leaflet-tile-container {
	width: 1600px;
	height: 1600px;
	-webkit-transform-origin: 0 0;
	}
.leaflet-marker-icon,
.leaflet-marker-shadow {
	display: block;
	}
/* .leaflet-container svg: reset svg max-width decleration shipped in Joomla! (joomla.org) 3.x */
/* .leaflet-container img: map is broken in FF if you have max-width: 100% on tiles */
.leaflet-container .leaflet-overlay-pane svg {
	max-width: none !important;
	max-height: none !important;
	}
.leaflet-container .leaflet-marker-pane img,
.leaflet-container .leaflet-shadow-pane img,
.leaflet-container .leaflet-tile-pane img,
.leaflet-container img.leaflet-image-layer,
.leaflet-container .leaflet-tile {
	max-width: none !important;
	max-height: none !important;
	width: auto;
	padding: 0;
	}

.leaflet-container.leaflet-touch-zoom {
	-ms-touch-action: pan-x pan-y;
	touch-action: pan-x pan-y;
	}
.leaflet-container.leaflet-touch-drag {
	-ms-touch-action: pinch-zoom;
	/* Fallback for FF which doesn't support pinch-zoom */
	touch-action: none;
	touch-action: pinch-zoom;
}
.leaflet-container.leaflet-touch-drag.leaflet-touch-zoom {
	-ms-touch-action: none;
	touch-action: none;
}
.leaflet-container {
	-webkit-tap-highlight-color: transparent;
}
.leaflet-container a {
	-webkit-tap-highlight-color: rgba(51, 181, 229, 0.4);
}
.leaflet-tile {
	filter: inherit;
	visibility: hidden;
	}
.leaflet-tile-loaded {
	visibility: inherit;
	}
.leaflet-zoom-box {
	width: 0;
	height: 0;
	-moz-box-sizing: border-box;
	     box-sizing: border-box;
	z-index: 800;
	}
/* workaround for https://bugzilla.mozilla.org/show_bug.cgi?id=888319 */
.leaflet-overlay-pane svg {
	-moz-user-select: none;
	}

.leaflet-pane         { z-index: 400; }

.leaflet-tile-pane    { z-index: 200; }
.leaflet-overlay-pane { z-index: 400; }
.leaflet-shadow-pane  { z-index: 500; }
.leaflet-marker-pane  { z-index: 600; }
.leaflet-tooltip-pane   { z-index: 650; }
.leaflet-popup-pane   { z-index: 700; }

.leaflet-map-pane canvas { z-index: 100; }
.leaflet-map-pane svg    { z-index: 200; }

.leaflet-vml-shape {
	width: 1px;
	height: 1px;
	}
.lvml {
	behavior: url(#default#VML);
	display: inline-block;
	position: absolute;
	}


/* control positioning */

.leaflet-control {
	position: relative;
	z-index: 800;
	pointer-events: visiblePainted; /* IE 9-10 doesn't have auto */
	pointer-events: auto;
	}
.leaflet-top,
.leaflet-bottom {
	position: absolute;
	z-index: 1000;
	pointer-events: none;
	}
.leaflet-top {
	top: 0;
	}
.leaflet-right {
	right: 0;
	}
.leaflet-bottom {
	bottom: 0;
	}
.leaflet-left {
	left: 0;
	}
.leaflet-control {
	float: left;
	clear: both;
	}
.leaflet-right .leaflet-control {
	float: right;
	}
.leaflet-top .leaflet-control {
	margin-top: 10px;
	}
.leaflet-bottom .leaflet-control {
	margin-bottom: 10px;
	}
.leaflet-left .leaflet-control {
	margin-left: 10px;
	}
.leaflet-right .leaflet-control {
	margin-right: 10px;
	}


/* zoom and fade animations */

.leaflet-fade-anim .leaflet-popup {
	opacity: 0;
	-webkit-transition: opacity 0.2s linear;
	   -moz-transition: opacity 0.2s linear;
	        transition: opacity 0.2s linear;
	}
.leaflet-fade-anim .leaflet-map-pane .leaflet-popup {
	opacity: 1;
	}
.leaflet-zoom-animated {
	-webkit-transform-origin: 0 0;
	    -ms-transform-origin: 0 0;
	        transform-origin: 0 0;
	}
svg.leaflet-zoom-animated {
	will-change: transform;
}

.leaflet-zoom-anim .leaflet-zoom-animated {
	-webkit-transition: -webkit-transform 0.25s cubic-bezier(0,0,0.25,1);
	   -moz-transition:    -moz-transform 0.25s cubic-bezier(0,0,0.25,1);
	        transition:         transform 0.25s cubic-bezier(0,0,0.25,1);
	}
.leaflet-zoom-anim .leaflet-tile,
.leaflet-pan-anim .leaflet-tile {
	-webkit-transition: none;
	   -moz-transition: none;
	        transition: none;
	}

.leaflet-zoom-anim .leaflet-zoom-hide {
	visibility: hidden;
	}

/* cursors */

.leaflet-interactive {
	cursor: pointer;
	}
.leaflet-grab {
	cursor: -webkit-grab;
	cursor:    -moz-grab;
	cursor:         grab;
	}
.leaflet-crosshair,
.leaflet-crosshair .leaflet-interactive {
	cursor: crosshair;
	}
.leaflet-popup-pane,
.leaflet-control {
	cursor: auto;
	}
.leaflet-dragging .leaflet-grab,
.leaflet-dragging .leaflet-grab .leaflet-interactive,
.leaflet-dragging .leaflet-marker-draggable {
	cursor: move;
	cursor: -webkit-grabbing;
	cursor:    -moz-grabbing;
	cursor:         grabbing;
	}

/* marker & overlays interactivity */
.leaflet-marker-icon,
.leaflet-marker-shadow,
.leaflet-image-layer,
.leaflet-pane > svg path,
.leaflet-tile-container {
	pointer-events: none;
	}

.leaflet-marker-icon.leaflet-interactive,
.leaflet-image-layer.leaflet-interactive,
.leaflet-pane > svg path.leaflet-interactive,
svg.leaflet-image-layer.leaflet-interactive path {
	pointer-events: visiblePainted; /* IE 9-10 doesn't have auto */
	pointer-events: auto;
	}

/* visual tweaks */

.leaflet-container {
	background: #ddd;
	outline-offset: 1px;
	}
.leaflet-container a {
	color: #0078A8;
	}
.leaflet-zoom-box {
	border: 2px dotted #38f;
	background: rgba(255,255,255,0.5);
	}


/* general typography */
.leaflet-container {
	font-family: "Helvetica Neue", Arial, Helvetica, sans-serif;
	font-size: 12px;
	font-size: 0.75rem;
	line-height: 1.5;
	}


/* general toolbar styles */

.leaflet-bar {
	box-shadow: 0 1px 5px rgba(0,0,0,0.65);
	border-radius: 4px;
	}
.leaflet-bar a {
	background-color: #fff;
	border-bottom: 1px solid #ccc;
	width: 26px;
	height: 26px;
	line-height: 26px;
	display: block;
	text-align: center;
	text-decoration: none;
	color: black;
	}
.leaflet-bar a,
.leaflet-control-layers-toggle {
	background-position: 50% 50%;
	background-repeat: no-repeat;
	display: block;
	}
.leaflet-bar a:hover,
.leaflet-bar a:focus {
	background-color: #f4f4f4;
	}
.leaflet-bar a:first-child {
	border-top-left-radius: 4px;
	border-top-right-radius: 4px;
	}
.leaflet-bar a:last-child {
	border-bottom-left-radius: 4px;
	border-bottom-right-radius: 4px;
	border-bottom: none;
	}

.leaflet-bar a.leaflet-disabled {
	cursor: default;
	background-color: #f4f4f4;
	color: #bbb;
	}

.leaflet-touch .leaflet-bar a {
	width: 30px;
	height: 30px;
	line-height: 30px;
	}
.leaflet-touch .leaflet-bar a:first-child {
	border-top-left-radius: 2px;
	border-top-right-radius: 2px;
	}
.leaflet-touch .leaflet-bar a:last-child {
	border-bottom-left-radius: 2px;
	border-bottom-right-radius: 2px;
	}

/* zoom control */

.leaflet-control-zoom-in,
.leaflet-control-zoom-out {
	font: bold 18px 'Lucida Console', Monaco, monospace;
	text-indent: 1px;
	}

.leaflet-touch .leaflet-control-zoom-in, .leaflet-touch .leaflet-control-zoom-out  {
	font-size: 22px;
	}


/* layers control */

.leaflet-control-layers {
	box-shadow: 0 1px 5px rgba(0,0,0,0.4);
	background: #fff;
	border-radius: 5px;
	}
.leaflet-control-layers-toggle {
	background-image: url(images/layers.png);
	width: 36px;
	height: 36px;
	}
.leaflet-retina .leaflet-control-layers-toggle {
	background-image: url(images/layers-2x.png);
	background-size: 26px 26px;
	}
.leaflet-touch .leaflet-control-layers-toggle {
	width: 44px;
	height: 44px;
	}
.leaflet-control-layers .leaflet-control-layers-list,
.leaflet-control-layers-expanded .leaflet-control-layers-toggle {
	display: none;
	}
.leaflet-control-layers-expanded .leaflet-control-layers-list {
	display: block;
	position: relative;
	}
.leaflet-control-layers-expanded {
	padding: 6px 10px 6px 6px;
	color: #333;
	background: #fff;
	}
.leaflet-control-layers-scrollbar {
	overflow-y: scroll;
	overflow-x: hidden;
	padding-right: 5px;
	}
.leaflet-control-layers-selector {
	margin-top: 2px;
	position: relative;
	top: 1px;
	}
.leaflet-control-layers label {
	display: block;
	font-size: 13px;
	font-size: 1.08333em;
	}
.leaflet-control-layers-separator {
	height: 0;
	border-top: 1px solid #ddd;
	margin: 5px -10px 5px -6px;
	}

/* Default icon URLs */
.leaflet-default-icon-path { /* used only in path-guessing heuristic, see L.Icon.Default */
	background-image: url(images/marker-icon.png);
	}


/* attribution and scale controls */

.leaflet-container .leaflet-control-attribution {
	background: #fff;
	background: rgba(255, 255, 255, 0.8);
	margin: 0;
	}
.leaflet-control-attribution,
.leaflet-control-scale-line {
	padding: 0 5px;
	color: #333;
	line-height: 1.4;
	}
.leaflet-control-attribution a {
	text-decoration: none;
	}
.leaflet-control-attribution a:hover,
.leaflet-control-attribution a:focus {
	text-decoration: underline;
	}
.leaflet-control-attribution svg {
	display: inline !important;
	}
.leaflet-left .leaflet-control-scale {
	margin-left: 5px;
	}
.leaflet-bottom .leaflet-control-scale {
	margin-bottom: 5px;
	}
.leaflet-control-scale-line {
	border: 2px solid #777;
	border-top: none;
	line-height: 1.1;
	padding: 2px 5px 1px;
	white-space: nowrap;
	overflow: hidden;
	-moz-box-sizing: border-box;
	     box-sizing: border-box;

	background: #fff;
	background: rgba(255, 255, 255, 0.5);
	}
.leaflet-control-scale-line:not(:first-child) {
	border-top: 2px solid #777;
	border-bottom: none;
	margin-top: -2px;
	}
.leaflet-control-scale-line:not(:first-child):not(:last-child) {
	border-bottom: 2px solid #777;
	}

.leaflet-touch .leaflet-control-attribution,
.leaflet-touch .leaflet-control-layers,
.leaflet-touch .leaflet-bar {
	box-shadow: none;
	}
.leaflet-touch .leaflet-control-layers,
.leaflet-touch .leaflet-bar {
	border: 2px solid rgba(0,0,0,0.2);
	background-clip: padding-box;
	}


/* popup */

.leaflet-popup {
	position: absolute;
	text-align: center;
	margin-bottom: 20px;
	}
.leaflet-popup-content-wrapper {
	padding: 1px;
	text-align: left;
	border-radius: 12px;
	}
.leaflet-popup-content {
	margin: 13px 24px 13px 20px;
	line-height: 1.3;
	font-size: 13px;
	font-size: 1.08333em;
	min-height: 1px;
	}
.leaflet-popup-content p {
	margin: 17px 0;
	margin: 1.3em 0;
	}
.leaflet-popup-tip-container {
	width: 40px;
	height: 20px;
	position: absolute;
	left: 50%;
	margin-top: -1px;
	margin-left: -20px;
	overflow: hidden;
	pointer-events: none;
	}
.leaflet-popup-tip {
	width: 17px;
	height: 17px;
	padding: 1px;

	margin: -10px auto 0;
	pointer-events: auto;

	-webkit-transform: rotate(45deg);
	   -moz-transform: rotate(45deg);
	    -ms-transform: rotate(45deg);
	        transform: rotate(45deg);
	}
.leaflet-popup-content-wrapper,
.leaflet-popup-tip {
	background: white;
	color: #333;
	box-shadow: 0 3px 14px rgba(0,0,0,0.4);
	}
.leaflet-container a.leaflet-popup-close-button {
	position: absolute;
	top: 0;
	right: 0;
	border: none;
	text-align: center;
	width: 24px;
	height: 24px;
	font: 16px/24px Tahoma, Verdana, sans-serif;
	color: #757575;
	text-decoration: none;
	background: transparent;
	}
.leaflet-container a.leaflet-popup-close-button:hover,
.leaflet-container a.leaflet-popup-close-button:focus {
	color: #585858;
	}
.leaflet-popup-scrolled {
	overflow: auto;
	border-bottom: 1px solid #ddd;
	border-top: 1px solid #ddd;
	}

.leaflet-oldie .leaflet-popup-content-wrapper {
	-ms-zoom: 1;
	}
.leaflet-oldie .leaflet-popup-tip {
	width: 24px;
	margin: 0 auto;

	-ms-filter: "progid:DXImageTransform.Microsoft.Matrix(M11=0.70710678, M12=0.70710678, M21=-0.70710678, M22=0.70710678)";
	filter: progid:DXImageTransform.Microsoft.Matrix(M11=0.70710678, M12=0.70710678, M21=-0.70710678, M22=0.70710678);
	}

.leaflet-oldie .leaflet-control-zoom,
.leaflet-oldie .leaflet-control-layers,
.leaflet-oldie .leaflet-popup-content-wrapper,
.leaflet-oldie .leaflet-popup-tip {
	border: 1px solid #999;
	}


/* div icon */

.leaflet-div-icon {
	background: #fff;
	border: 1px solid #666;
	}


/* Tooltip */
/* Base styles for the element that has a tooltip */
.leaflet-tooltip {
	position: absolute;
	padding: 6px;
	background-color: #fff;
	border: 1px solid #fff;
	border-radius: 3px;
	color: #222;
	white-space: nowrap;
	-webkit-user-select: none;
	-moz-user-select: none;
	-ms-user-select: none;
	user-select: none;
	pointer-events: none;
	box-shadow: 0 1px 3px rgba(0,0,0,0.4);
	}
.leaflet-tooltip.leaflet-interactive {
	cursor: pointer;
	pointer-events: auto;
	}
.leaflet-tooltip-top:before,
.leaflet-tooltip-bottom:before,
.leaflet-tooltip-left:before,
.leaflet-tooltip-right:before {
	position: absolute;
	pointer-events: none;
	border: 6px solid transparent;
	background: transparent;
	content: "";
	}

/* Directions */

.leaflet-tooltip-bottom {
	margin-top: 6px;
}
.leaflet-tooltip-top {
	margin-top: -6px;
}
.leaflet-tooltip-bottom:before,
.leaflet-tooltip-top:before {
	left: 50%;
	margin-left: -6px;
	}
.leaflet-tooltip-top:before {
	bottom: 0;
	margin-bottom: -12px;
	border-top-color: #fff;
	}
.leaflet-tooltip-bottom:before {
	top: 0;
	margin-top: -12px;
	margin-left: -6px;
	border-bottom-color: #fff;
	}
.leaflet-tooltip-left {
	margin-left: -6px;
}
.leaflet-tooltip-right {
	margin-left: 6px;
}
.leaflet-tooltip-left:before,
.leaflet-tooltip-right:before {
	top: 50%;
	margin-top: -6px;
	}
.leaflet-tooltip-left:before {
	right: 0;
	margin-right: -12px;
	border-left-color: #fff;
	}
.leaflet-tooltip-right:before {
	left: 0;
	margin-left: -12px;
	border-right-color: #fff;
	}

/* Printing */

@media print {
	/* Prevent printers from removing background-images of controls. */
	.leaflet-control {
		-webkit-print-color-adjust: exact;
		color-adjust: exact;
		}
	}
"""

            with open(f"{dir_base}/content/mysite/leaflet.css", "w") as resource_file:
                resource_file.write(resource_leaflet_css)


            leaflet_icon = pkg_resources.resource_stream(__name__, "images/marker-icon.png")
            leaflet_icon_data = leaflet_icon.read()

            with open(f"{dir_base}/content/mysite/leaflet-icon.png", "wb") as resource_file:
                resource_file.write(leaflet_icon_data)


            leaflet_shadow = pkg_resources.resource_stream(__name__, "images/marker-shadow.png")
            leaflet_shadow_data = leaflet_shadow.read()

            with open(f"{dir_base}/content/mysite/leaflet-shadow.png", "wb") as resource_file:
                resource_file.write(leaflet_shadow_data)

            leaflet_icon_2x = pkg_resources.resource_stream(__name__, "images/marker-icon-2x.png")
            leaflet_icon_2x_data = leaflet_icon_2x.read()

            with open(f"{dir_base}/content/mysite/leaflet-icon-2x.png", "wb") as resource_file:
                resource_file.write(leaflet_icon_2x_data)
            
            with open(f"{dir_base}/content/mysite/map/{public_name}/index.qmd", "w") as hugo_file:
                hugo_file.write("---\n")
                hugo_file.write(f"title: \"Map\"\n")
                hugo_file.write("listing:\n")
                hugo_file.write("  template: map.ejs\n")
                hugo_file.write("page-layout: full\n")
                hugo_file.write("---\n")

        # TODO copy map.ejs


class Data(View):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def write(self, dir_base = None):

        if self.slug is None:
          public_name = self.primitive.lower()
        else:
          public_name = self.slug

        Path(f"{dir_base}/content/mysite/data/{public_name}").mkdir(parents=True, exist_ok=True)

        for data_file in self.data_files:

            name,ext = data_file.split(".")

            db = sqlite_utils.Database(f"{dir_base}/content/mysite/data/{public_name}/{name}.db")

            # Read in CSV and write out to DB

            with open(data_file, newline='') as csvfile:
                data_reader = csv.DictReader(csvfile)

                for row in data_reader:
                  db[name].insert(row)

        with open(f"{dir_base}/content/mysite/data/{public_name}/index.qmd", "w") as hugo_file:
          hugo_file.write("---\n")
          hugo_file.write(f"title: \"Data\"\n")
          hugo_file.write("listing:\n")
          hugo_file.write("  template: data.ejs\n")
          hugo_file.write("page-layout: full\n")
          hugo_file.write("---\n")
        
