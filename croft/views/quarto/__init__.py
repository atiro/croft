from pathlib import Path
import sqlite_utils
import csv

class Quarto:

    def __init__(self, keep_nav_names=False, config=None):
        self.views = {}
        self._keep_nav_names = keep_nav_names
        self._config = config

    def add_view(self, view = None):
        # TODO - retrueve URL and name
        name = view.name
        view_type = view.__class__.__name__.lower()
        if view_type not in self.views:
            self.views[view_type] = {}

        self.views[view_type][name] = {}
#        self.views[view_type][name]['view'] = view.__class__.__name__.lower()
        self.views[view_type][name]['slug'] = view.slug
        self.views[view_type][name]['name'] = view.name
        self.views[view_type][name]['primary'] = view.primary

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
  title: {self._config['site']['title']}
  navbar:
    background: primary
    left:
      - href: index.qmd
        text: Home"""

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
        # If more than one of this type, only the primary is written here, the other(s)
        # go in side nav switcher. We also use either the view type name or user set name
       primary_item = ""
       submenu_items = ""
       for view in self.views[view_type]:
         if self.views[view_type][view]['primary']:
           if len(self.views[view_type]) > 1:
             primary_item = f"""
        - text: {self.views[view_type][view]['name'] if self._keep_nav_names else view_type.capitalize()}
          href: {view_type}/{self.views[view_type][view]['slug']}/index.qmd"""
           else:
             primary_item = f"""
      - text: {self.views[view_type][view]['name'] if self._keep_nav_names else view_type.capitalize()}
        href: {view_type}/{self.views[view_type][view]['slug']}/index.qmd"""
         else:
           submenu_items += f"""
        - text: {self.views[view_type][view]['name']}
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
        homepage_file.write(f"title: \"Home\"\n")
        homepage_file.write("---\n")
        homepage_file.write(self._config['site']['intro'])

      with open(f"{dir_base}/content/mysite/_quarto.yml", "w") as quarto_file:
        quarto_file.write(project_config + website_config + format_config)

class View:

    def __init__(self, datasource = None, primitive = None, slug = None, name = None, link = None, primary= False):
        self._primitive = primitive
        self._slug = slug
        self._name = name
        self._link = link
        self._primary = primary
        self.statements = datasource.statements
        self.data_files = datasource.data_files

    @property
    def name(self):
        return self._name

    @property
    def slug(self):
        return self._slug

    @property
    def primitive(self):
        return self._primitive

    @property
    def link(self):
        return self._link

    @property
    def primary(self):
        return self._primary

class Gallery(View):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def write(self, dir_base = None):

       if self.slug is None:
         public_name = self.primitive.lower()
       else:
         public_name = self.slug

       Path(f"{dir_base}/content/mysite/gallery/{public_name}").mkdir(parents=True, exist_ok=True)

       print(f"Writing gallery out for primitive {self.primitive}")

       for gall_item in self.statements:

            filename = self.statements[gall_item]["_filename_"]

            fields = self.statements[gall_item][self.primitive].get_primary_fields()
            print(f"Getting for {gall_item} {self.primitive}")
            if len(fields) == 0:
              # If this item doesn't have anything set for the primitive wanted for this view, skip
              print(f"No values set for {gall_item}, skipping")
              continue

            with open(f"{dir_base}/content/mysite/gallery/{public_name}/{filename}.qmd", "w") as hugo_file:
                hugo_file.write("---\n")

                hugo_file.write(f"title: \"{fields['Name']}\"\n")
                hugo_file.write(f"description: \"{fields['Description']}\"\n")

                hugo_file.write("date: 2021-06-26T17:50:41+01:00\n")
                hugo_file.write("draft: false\n")
                hugo_file.write(f"type: {public_name}\n")
                hugo_file.write("---\n")

            with open(f"{dir_base}/content/mysite/gallery/{public_name}/index.qmd", "w") as hugo_file:
                hugo_file.write("---\n")
                hugo_file.write(f"title: \"Gallery\"\n")
                hugo_file.write("listing:\n")
                hugo_file.write("  filter-ui: true\n")
                hugo_file.write("  type: grid\n")
                hugo_file.write("---\n")

class Table(View):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def write(self, dir_base = None):

        if self.slug is None:
          public_name = self.primitive.lower()
        else:
          public_name = self.slug

        Path(f"{dir_base}/content/mysite/table/{public_name}").mkdir(parents=True, exist_ok=True)

        for gall_item in self.statements:
            primitive_fields = self.statements[gall_item][self.primitive].get_primary_fields()
            link_fields = None
            if self.link:
              link_fields = self.statements[gall_item][self.link].get_primary_fields()

            if 'Name' not in primitive_fields:
               # Nothing set for this, ignore (e.g. has Actor values but not Event values)
               continue

            filename = self.statements[gall_item]["_filename_"]

            with open(f"{dir_base}/content/mysite/table/{public_name}/{filename}.qmd", "w") as hugo_file:
                hugo_file.write("---\n")

                print(primitive_fields)

                hugo_file.write(f"title: \"{primitive_fields['Name']}\"\n")
                # TODO how do we know this is correct ? I think is a config setting need to pickup
                # This should all be configured, diff primitives use diff fields
                if link_fields: 
                  hugo_file.write(f"author: \"{link_fields['Name']}\"\n")

                hugo_file.write(f"description: \"{primitive_fields['Description']}\"\n")

                hugo_file.write("date: 2021-06-26T17:50:41+01:00\n")
                hugo_file.write("draft: false\n")
                hugo_file.write(f"type: {public_name}\n")
                hugo_file.write("---\n")

            # Need to map from our fields to the known Quarto fields (date, author, title..) based on
            # the config file settings

            with open(f"{dir_base}/content/mysite/table/{public_name}/index.qmd", "w") as hugo_file:
                hugo_file.write("---\n")
                hugo_file.write(f"title: \"Table\"\n")
                hugo_file.write("listing:\n")
                hugo_file.write("  type: table\n")
                hugo_file.write("  field-display-names:\n    author: \"Institution\"\n    title: \"Experience\"\n")
                hugo_file.write("  fields: [date, author, title]\n")
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

        for map_item in self.statements:
            primitive_fields = self.statements[map_item][self.primitive].get_primary_fields()
            if self.link != None:
              link_fields = self.statements[map_item][self.link].get_primary_fields()

            if 'Name' not in primitive_fields:
               # Nothing set for this, ignore (e.g. has Actor values but not Event values)
               # TODO try link primitive fields
               continue

            filename = self.statements[map_item]["_filename_"]

            with open(f"{dir_base}/content/mysite/map/{public_name}/{filename}.qmd", "w") as hugo_file:
                hugo_file.write("---\n")

                print(primitive_fields)

                hugo_file.write(f"title: \"{primitive_fields['Name']}\"\n")
                hugo_file.write(f"lat: \"{primitive_fields['Location::Lat']}\"\n")
                hugo_file.write(f"lon: \"{primitive_fields['Location::Lon']}\"\n")
                # XX how do we know this is correct ? I think is a config setting need to pickup
                if link_fields: 
                  hugo_file.write(f"author: \"{link_fields['Name']}\"\n")
                hugo_file.write(f"description: \"{primitive_fields['Description']}\"\n")

                hugo_file.write("date: 2021-06-26T17:50:41+01:00\n")
                hugo_file.write("draft: false\n")
                hugo_file.write(f"type: {public_name}\n")
                hugo_file.write("---\n")

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
        
