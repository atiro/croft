import csv
import json
from pathvalidate import sanitize_filename
from pathlib import Path
from croft.datasource import DataSource

HUGO_BASE = ""

content = []
global_content = {} # This stores

# Read in Config - this needs to say which CSVs to read, which columns go where in the data 
# model, and what links between different files (shared identifiers)

with open('croft-config.json') as config_file:
    config = json.load(config_file)

# Set the base location for Hugo to build in
HUGO_BASE = config['paths']['hugo_base']

# TODO read in site config and write out hugo config.toml

# Read in (possibly multiple) CSV

for data_file in config['source']: # 
  # TODO check if CSV or JSON or something else...

  ds = new DataSource(data_file)

  values = {}

  ## TODO - Should parse all the config first, then call this on each data source as an object

  print(f"Parsing file {data_file['filename']}")

  with open(data_file['filename']) as csv_file:
    reader = csv.DictReader(csv_file)
    for row in reader:
        # Save all the data from this row with new primitive based keys
        row_content = {}
  # We now write out the reelvant hugo markdown files based on the mapping from croft-config
     
        # TODO cache this instead of on every loop
        for mapping in data_file['mapping']:
           # Column to look for in CSV
           column = mapping[0]
           # New field name used 
           destination = mapping[1]
           # Alias in primitive names not wanted (e.g. Actor -> Author)
           alt_name = None
           if len(mapping) > 2:
               print(f"GOt alt name f{mapping[2]}")
               alt_name = mapping[2]
           primitive, meta_field = destination.split('/', 1)
           meta_field = meta_field.lower()
           # Only if we want to output it, and if the row has a value for this
           print(f"Output {output_fields}")
           print(f"{primitive}")
           # Check if we should be outputing this data from this mapping (if it exists in the CSV)
           if primitive in output_fields and row[column] is not None:
             print(f"Saving content for {column}")
             # Check if initialised yet
             if primitive not in row_content:
               print("Initialising row content")
               row_content[primitive] = {}
             # TODO special meta_field like DateParsed that should do something with the data
#             if primitive == "Event" and meta_field == "DateText":
             print(f"Adding {row[column]} {alt_name}")
             # Save the data and the preferred alt_name
             row_content[primitive][meta_field] = [row[column], alt_name]
         # TODO - could there be another fundamnetal type refereend that is not the link field ?

           if column == link_field:
             # Save the join field TODO - more than one ?
             row_content["_link_"] = row[column]

         # TODO is there is only one file to output per row (+ keys linking?)
         # TODO there might not be an output file
           if column == key_field:
             print(f"Adding key field {primitive} {column}")
             row_content[primitive]["_filename_"] = sanitize_filename(row[column]).replace(" ", "-").lower()
             row_content[primitive]["_title_"] = row[column]

        content.append(row_content)
        # If this is linked to other data we save everything on the link value for use later on in outputs
        # that combine more than one primitive (as opposed to a primitive output that combines data, confusing?!)

        # First we check if the link field exists in the data row
        if "_link_" in row_content:
          if row_content["_link_"] not in global_content:
            # No existing linkages, start an array
            global_content[row_content["_link_"]] = []
          # Now we go through the row looking for data to extract
          global_row = {}
          for primitive in row_content:
            print(f"Primitive: {primitive}")
            if primitive.startswith("_"):
              continue
            # Save all the meta fields (Title, etc) attached to a primitive (Event, Participant, etc) for this row
            for meta_field in row_content[primitive]:
                # TODO avoid overwriting link primitive
                if meta_field.startswith("_"):
                    continue
                print(f"Global: {row_content['_link_']} - {primitive}/{meta_field.title()}")
                # TODO - this only allows one datum per linked key, need to support multiple
                global_row[f"{primitive}/{meta_field.title()}"] = row_content[primitive][meta_field]

          # Save this data row on the linked value
          global_content[row_content["_link_"]].append(global_row)

      # TODO make content path if not there

      # TODO check file doesn't already exist
      # TODO slugify keyfield to make save for filename
        # TODO - handle deeper depth than 1

  print("Writing primitives output")

  # First output is for the gallery view, which needs real pages creating for each Participant
  # and then a listing view over them all.

  # The slug controls the public name instead of 'Participant'

  gallery_config = config["output"]["gallery"]
  gallery_primitive = gallery_config["primitive"]
  gallery_slug = gallery_config["slug"]

  # Loop over data from this CSV
  for item in content:
    # GO over primitives
    for primitive in item:
      print(f"Type {primitive}")
      if primitive.startswith("_"):
        # Ignore special case internal fields such as _filename
        continue
      filename = item[primitive]["_filename_"]
      if primitive == gallery_slug:
        public_name = gallery_slug
      else:
        public_name = primitive.lower()

      # Create directory
      Path(f"{HUGO_BASE}/content/gallery/{public_name}").mkdir(parents=True, exist_ok=True)

      with open(f"{HUGO_BASE}/content/gallery/{public_name}/{filename}.md", "w") as hugo_file:
          hugo_file.write("---\n")
          # TODO exclude field starting with _
          for field in item[primitive]:
            print(f"Field - {field}")
            if not field.startswith("_"):
              datum,alt_name = item[primitive][field]
              field_name = field
              if alt_name != None:
                field_name = alt_name
              if "[]" in field_name:
                  # TODO allow multiple values in file, split them here
                hugo_file.write(f"{field_name}:\n  - \"{datum}\"\n")
              else:
                hugo_file.write(f"{field_name}: \"{datum}\"\n")
          if "_link_" in item:
              # TODO handle multiple
              hugo_file.write(f"Participants: \n  - {item['_link_']}\n")

          hugo_file.write("date: 2021-06-26T17:50:41+01:00\n")
          hugo_file.write("draft: false\n")
          hugo_file.write(f"type: {public_name}\n")
          hugo_file.write("---\n")

  print("Writing secondary outputs")

  # TODO - this should read in from output in config file, hardcoded to maps at the moment

with open("test.json", "w") as test_file:
    json.dump(global_content, test_file)

## TODO - output files depending on which components (Table, Map, etc) are enabled in config

map_config = config['output']['map']
with open(f"{HUGO_BASE}/data/map/{map_config['name']}.json", "w") as data_file:
      # We construct the data and then write it out as JSON
    map_data = { "points": [] }
    for linked_data in global_content:
        ## TODO we may or may not only want to show once if the same Actor is linked multiple times, should be config
        ## option. Here we hard code to take the first one only per Actor
        datum = {}
        for map_field,primitive_field in map_config["display"]["point"].items():
            if '/' in map_field:
                map_field_1, map_field_2 = map_field.split('/')
                if map_field_1 not in datum:
                  datum[map_field_1] = {}
                datum[map_field_1][map_field_2] = global_content[linked_data][0][primitive_field][0]
            else:
                print(f"{linked_data}{primitive_field}")
                datum[map_field] = global_content[linked_data][0][primitive_field][0]
        map_data["points"].append(datum)
    json.dump(map_data, data_file)
    # TODO connected points (pointA, pointB, direction of connection)

## TODO - check if table output wanted
table_config = config['output']['table']
print("Output: Table")
with open(f"{HUGO_BASE}/data/table/{table_config['name']}.json", "w") as data_file:
    table_data = { "columns": [], "data": [] }

    # Get name for column in table, and the field name to access the data
    for table_column,primitive_field in table_config["dimensions"]:
        table_data["columns"].append(table_column)

    for linked_data in global_content:
        datum = []
        # Iterate thorugh all the times this actor is linked
        for actor_linked in global_content[linked_data]:
          # Build up rows for the table
          for table_column,primitive_field in table_config["dimensions"]:
            print(f"Looking up {linked_data}{primitive_field} in global content")
            try:
              datum.append(actor_linked[primitive_field][0])
            except:
            # Doesn't exist in the linked table. Skip it
              continue

          table_data["data"].append(datum)

    json.dump(table_data, data_file)

# TODO write out for Hugo/ Doks

#  - config.toml settings for Hugo / Doks
#  - layouts for basic and enabled plugins - indivudal and listing pages
#  - homepage layout based on enabled plugins

