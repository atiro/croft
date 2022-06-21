from pathlib import Path
import sqlite_utils 
import csv

class View:

    def __init(self, datasource = None, primitive = None, slug = None, name = None, link = None):
        self.primitive = primitive
        self.slug = slug
        self.name = name
        self.link = link
        self.statements = datasource.statements
        self.data_files = datasource.data_files

    def name(self):
        return self.name

    def slug(self):
        return self.slug

    def primitive(self):
        return self.primitive

class Gallery(View):

    def __init__(self, **kwargs):
        super().__init__(self, **kwargs)

    def write(self, dir_base = None):

       if self.slug is None:
         public_name = self.primitive.lower()
       else:
         public_name = self.slug

       Path(f"{dir_base}/content/mysite/gallery/{public_name}").mkdir(parents=True, exist_ok=True)

       print("Writing gallery out")

       for gall_item in self.statements:

            filename = self.statements[gall_item]["_filename_"]
            print(f"Writing gallery file for {filename}")

            with open(f"{dir_base}/content/mysite/gallery/{public_name}/{filename}.qmd", "w") as hugo_file:
                hugo_file.write("---\n")

                fields = self.statements[gall_item][self.primitive].get_primary_fields()

                hugo_file.write(f"title: \"{fields['Name']}\"\n")
                hugo_file.write(f"description: \"{fields['Description']}\"\n")

                hugo_file.write("date: 2021-06-26T17:50:41+01:00\n")
                hugo_file.write("draft: false\n")
                hugo_file.write(f"type: {public_name}\n")
                hugo_file.write("---\n")

            with open(f"{dir_base}/content/mysite/gallery/{public_name}/gallery.qmd", "w") as hugo_file:
                hugo_file.write("---\n")
                hugo_file.write(f"title: \"Gallery\"\n")
                hugo_file.write("listing:\n")
                hugo_file.write("  filter-ui: true\n")
                hugo_file.write("  type: grid\n")
                hugo_file.write("---\n")


class Table(View):

    def __init__(self, name = None, **kwargs):
        pass
#        super().__init__(self, **kwargs)

    def write(self, dir_base = None):

        Path(f"{dir_base}/content/mysite/table/").mkdir(parents=True, exist_ok=True)

        for gall_item in self.statements:
            primitive_fields = self.statements[gall_item][self.primitive].get_primary_fields()
            link_fields = self.statements[gall_item][self.link].get_primary_fields()

            if 'Name' not in primitive_fields:
               # Nothing set for this, ignore (e.g. has Actor values but not Event values)
               print("Skipping as Name not set")
               continue

            filename = self.statements[gall_item]["_filename_"]
            if self.slug is None:
              public_name = self.primitive.lower()
            else:
              public_name = self.slug

            Path(f"{dir_base}/content/mysite/table/{public_name}").mkdir(parents=True, exist_ok=True)

            with open(f"{dir_base}/content/mysite/table/{public_name}/{filename}.qmd", "w") as hugo_file:
                hugo_file.write("---\n")

                hugo_file.write(f"title: \"{primitive_fields['Name']}\"\n")
                # XX how do we know this is correct ? I think is a config setting need to pickup
                hugo_file.write(f"author: \"{link_fields['Name']}\"\n")

                hugo_file.write(f"description: \"{primitive_fields['Description']}\"\n")

                hugo_file.write("date: 2021-06-26T17:50:41+01:00\n")
                hugo_file.write("draft: false\n")
                hugo_file.write(f"type: {public_name}\n")
                hugo_file.write("---\n")

        with open(f"{dir_base}/content/mysite/table/{public_name}/index.qmd", "w") as hugo_file:
          hugo_file.write("---\n")
          hugo_file.write(f"title: \"Table\"\n")
          hugo_file.write("listing:\n")
          hugo_file.write("  type: table\n")
          hugo_file.write("  field-display-names:\n    title: \"Experience\"\n    author: \"Institution\"\n")
          hugo_file.write("---\n")

class Data(View):

    def __init__(self, name = None, **kwargs):
        pass
#        super().__init__(self, **kwargs)

    def write(self, dir_base = None):

        Path(f"{dir_base}/content/mysite/data/").mkdir(parents=True, exist_ok=True)
        
        for data_file in self.data_files:

            name,ext = data_file.split(".")

            db = sqlite_utils.Database(f"{name}.db")

            # Read in CSV and write out to DB

            with open(data_file, newline='') as csvfile:
                data_reader = csv.reader(csvfile)

                db[name].insert_all(data_reader)

