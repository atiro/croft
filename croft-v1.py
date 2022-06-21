import csv
import json
from pathvalidate import sanitize_filename

HUGO_BASE = ""

content = []

# Read in Config - this needs to say which CSVs to read, which columns go where in the data 
# model, and what links between different files (shared identifiers)

with open('croft-config.json') as config_file:
    config = json.load(config_file)

HUGO_BASE = config['paths']['hugo_base']

# TODO read in site config and write out hugo config.toml

# Read in (possibly multiple) CSV

for data_file in config['data']:
  # TODO check if CSV or JSON or something else...
  fields = []
  key_field = data_file['key']
  link_field = None
  output_fields = data_file['output']

  if 'link' in data_file:
    link_field = data_file['link']

  for mapping in data_file['mapping']:
      fields.append(mapping[0])

  values = {}

  print(f"Parsing file {data_file['filename']}")
  with open(data_file['filename']) as csv_file:
    reader = csv.DictReader(csv_file)
    for row in reader:
        row_content = {}
#        values = {k: row[k] for k in fields}

  # We now write out the reelvant hugo markdown files based on the mapping
     
        # TODO cache this instead of on every loop
        for mapping in data_file['mapping']:
           column = mapping[0]
           destination = mapping[1]
           alt_name = None
           if len(mapping) > 2:
               print(f"GOt alt name f{mapping[2]}")
               alt_name = mapping[2]
           hugo_type, meta_field = destination.split('/', 1)
#           hugo_type = hugo_type.lower()
           meta_field = meta_field.lower()
           # Only if we want to output it, and if the row has a value for this
           print(f"Output {output_fields}")
           print(f"{hugo_type}")
           if hugo_type in output_fields and row[column] is not None:
             print(f"Saving content for {column}")
             # Check if initialised yet
             if hugo_type not in row_content:
               print("Initialising row content")
               row_content[hugo_type] = {}
             # TODO special meta_field like DateParsed that should do something with the data
             print(f"Adding {row[column]} {alt_name}")
             row_content[hugo_type][meta_field] = [row[column], alt_name]
         # TODO - could there be another fundamnetal type refereend that is not the link field ?

           if column == link_field:
             # How do we handle this in Hugo. DO we tag the interactive ?
             row_content["_link_"] = row[column]

         # TODO is there is only one file to output per row (+ keys linking?)
           if column == key_field:
             print(f"Adding key field {hugo_type} {column}")
             row_content[hugo_type]["_filename_"] = sanitize_filename(row[column]).replace(" ", "-").lower()
             row_content[hugo_type]["_title_"] = row[column]

        content.append(row_content)

      # TODO make content path if not there

      # TODO check file doesn't already exist
      # TODO slugify keyfield to make save for filename
        # TODO - handle deeper depth than 1

  print("Writing output")

  for item in content:
    for archetype in item:
      if archetype.startswith("_"):
        continue
      typename = archetype.lower()
      print(f"Type {archetype}")
      filename = item[archetype]["_filename_"]
      with open(f"{HUGO_BASE}/content/{typename}/{filename}.md", "w") as hugo_file:
          hugo_file.write("---\n")
          # TODO exclude field starting with _
          for field in item[archetype]:
            print(f"Field - {field}")
            if not field.startswith("_"):
              datum,alt_name = item[archetype][field]
              field_name = field
              if alt_name != None:
                field_name = alt_name
              if "[]" in field_name:
                  # TODO allow multiple values in file, split them here
                hugo_file.write(f"{field_name}:\n  - {datum}\n")
              else:
                hugo_file.write(f"{field_name}: {datum}\n")
          if "_link_" in item:
              # TODO handle multiple
              hugo_file.write(f"Participants: \n  - {item['_link_']}\n")

          hugo_file.write("date: 2021-06-26T17:50:41+01:00\n")
          hugo_file.write("draft: false\n")
          hugo_file.write("---\n")


# TODO write out for Hugo/ Doks

#  - config.toml settings for Hugo / Doks
#  - layouts for basic and enabled plugins - indivudal and listing pages
#  - homepage layout based on enabled plugins

