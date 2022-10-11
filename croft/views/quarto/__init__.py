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

            map_ejs = pkg_resources.resource_stream(__name__, "../../../resources/map/ejs/map.ejs")
            map_ejs_data = map_ejs.read()

            with open(f"{dir_base}/content/mysite/map/{public_name}/map.ejs", "w") as resource_file:
                resource_file.write(map_ejs_data)

            leaflet_marker_default_css = pkg_resources.resource_stream(__name__, "../../../resources/map/css/MarkerCluster.Default.css")
            leaflet_marker_default_css_data = leaflet_marker_default_css.read()

            with open(f"{dir_base}/content/mysite/MarkerCluster.Default.css", "wb") as resource_file:
                resource_file.write(leaflet_marker_default_css_data)

            leaflet_marker_css = pkg_resources.resource_stream(__name__, "../../../resources/map/css/MarkerCluster.css")
            leaflet_marker_css_data = leaflet_marker_css.read()

            with open(f"{dir_base}/content/mysite/MarkerCluster.css", "w") as resource_file:
                resource_file.write(leaflet_marker_css_data)

            leaflet_css = pkg_resources.resource_stream(__name__, "../../../resources/map/css/leaflet.css")
            leaflet_css_data = leaflet_css.read()

            with open(f"{dir_base}/content/mysite/leaflet.css", "w") as resource_file:
                resource_file.write(leaflet_css_data)

            leaflet_icon = pkg_resources.resource_stream(__name__, "../../../resources/map/images/marker-icon.png")
            leaflet_icon_data = leaflet_icon.read()

            with open(f"{dir_base}/content/mysite/leaflet-icon.png", "wb") as resource_file:
                resource_file.write(leaflet_icon_data)


            leaflet_shadow = pkg_resources.resource_stream(__name__, "../../../resources/map/images/marker-shadow.png")
            leaflet_shadow_data = leaflet_shadow.read()

            with open(f"{dir_base}/content/mysite/leaflet-shadow.png", "wb") as resource_file:
                resource_file.write(leaflet_shadow_data)

            leaflet_icon_2x = pkg_resources.resource_stream(__name__, "../../../resources/map/images/marker-icon-2x.png")
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
        
