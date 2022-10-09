import csv
from pathvalidate import sanitize_filename
from croft.primitive import Actor,Event,Place,Thing

class DataSource:
  """Handle the mapping of data from an external datasource (CSV file) to Croft data model"""

  ds_fields = []
  ds_mappings = []
  key_field = None
  link_field = None
  view_field = None

  # Knowledge Graph equiv, primitives and secondary attached to unique key (if only one
  # datasource, fake the key ?)

  statements = {}

  # Data to read in
  datasources = {}
  # How to show it in the output
  views = {}

  data_files = []

  def __init__(self, config):
      # Save mappings

      for source in config['source']:
        filename = source['filename']

        self.datasources[filename] = {}
        self.datasources[filename]['mappings'] = {}

        # This is used as the join key between different files
        if "key" in source:
          self.datasources[filename]['key'] = source["key"]

        if "view" in source:
          self.datasources[filename]['view'] = source["view"]

        if "link" in source:
          self.datasources[filename]['link'] = source["link"]

        if "display" in source:
          self.datasources[filename]['display'] = source["display"]

## TODO could we assume there is always a link primitive and (possibly) a single second primitve ?

        for mapping in source['mapping']:
          user_field, primitive,*alt_names = mapping
          alt_name = None
#          ds_fields.append(user_field)
#          ds_mappings.append(mapping)

#          if "/" in primitive:
#            primitive_type,primitive_field = primitive.split('/')
#          else:
          if "::" in primitive:
            primitive_type,primitive_field = primitive.split("::")

          if len(alt_names) > 0:
            alt_name = alt_names[0]

          self.datasources[filename]['mappings'][user_field] = {}
          self.datasources[filename]['mappings'][user_field]['primitive_type'] = primitive_type
          self.datasources[filename]['mappings'][user_field]['primitive_field'] = primitive_field
          self.datasources[filename]['mappings'][user_field]['alt_name'] = alt_name
          self.datasources[filename]['mappings'][user_field]['link'] = True if (source["link"] == user_field) else False
          self.datasources[filename]['mappings'][user_field]['display'] = True if (source["display"] == user_field) else False

        # Now we parse the data. Really we should do this in a sub class or this class should be called
        # Statements/Graph which creates a datasource per file.

        self.read_datasource(filename)

      for view in config['views']:
        self.views[view] = {}
        for attrib in config['views'][view]:
          self.views[view][attrib] = config['views'][view][attrib]

        # That's it!

  def map_column(self, filename, column):

     # Lookup column in mappings and return 

     print(f"Mapping from {filename} from column {column}")

     if column in self.datasources[filename]['mappings']:
       primitive = self.datasources[filename]['mappings'][column]['primitive_type']
       field = self.datasources[filename]['mappings'][column]['primitive_field']
     else:
       print("Unknown column referenced")
       return (None, None)

     return(primitive, field)

  def read_datasource(self, filename):
     """Read in the data and throw it at the primitives for writing out later"""
      # Read in CSV file

     print(f"Reading file {filename}")

     self.data_files.append(filename)
    
     with open(filename) as csv_file:
        reader = csv.DictReader(csv_file)
        link_primitive = None
        link_fieldname = None
        for row in reader:
          facts = []
          key_vals = []
          key_id = ""
          for col in row:
              if col != None and len(col) > 0:
                primitive, field = self.map_column(filename, col)
              else:
                print("CSV file contains extra column on line X, ignoring")
                continue

              if primitive == None:
                  continue

              if col in self.datasources[filename]['key']:
                  print(f"Col {col} is in keys")
                  key_vals.append(row[col])
              else:
                  # No key, applies to all rows that have same link val
                  print(f"Col {col} not in keys")

              if self.datasources[filename]['mappings'][col]['link']:
                link_id = row[col] # we have to iterate through all matching
                print(f"Fact (link): {primitive}/{field}/{row[col]}")
                facts.append([primitive, field, row[col]])
              else:
                print(f"Fact: {primitive}/{field}/{row[col]}")
                facts.append([primitive, field, row[col]])

          if key_vals:
            key_id = "-".join(key_vals)
          print(f"Key ID: {key_id} {key_vals}")

          # If we've not seen anything for this statement before, initilise it

          # TODO should iterate here through all that match on link_id
          if link_id not in self.statements:
             print(f"Creating link id for {link_id}")
             self.statements[link_id] = {}
          else:
              print(f"Link id {link_id} already exists")

          if key_id and key_id not in self.statements[link_id]:
               print(f"Creating key id for {key_id}")
               self.statements[link_id][key_id] = {}
               self.statements[link_id][key_id]['Actor'] = Actor()
               self.statements[link_id][key_id]['Place'] = Place()
               self.statements[link_id][key_id]['Thing'] = Thing()
               self.statements[link_id][key_id]['Event'] = Event()
               self.statements[link_id][key_id]['_filename_'] = sanitize_filename(key_id).replace(" ", "-").lower()
               self.statements[link_id][key_id]['_title_'] = link_id
          else:
              print(f"Key id {key_id} already exists")

           # Now add all the associated facts for this statement

          for fact in facts:
             fact_type = fact[0]
             print(f"Setting fact {fact_type} for link_id {link_id} Name: {fact[1]} Value: {fact[2]}")
             # Can use match/case when python 3.10 widely used...
             if (fact_type == "Actor") or (fact_type == "Event") or (fact_type == "Place") or (fact_type == "Thing"):
                 if key_id:
                   print(f"Setting field {fact[1]} val {fact[2]} for single link: {link_id} key: {key_id}")
                   self.statements[link_id][key_id][fact_type].set_primary_field(fact[1], fact[2])
                 else:
                   # Applies to all facts with same link 
                   for known_key_id in self.statements[link_id]:
                     print(f"Setting field {fact[1]} val {fact[2]} for link: {link_id} key: {known_key_id}")
                     self.statements[link_id][known_key_id][fact_type].set_primary_field(fact[1], fact[2])

             elif ((fact_type == "Measurement") or (fact_type == "Observation") or (fact_type == "Text") or (fact_type == "Document")):
                    self.statements[link_id][key_id][link_primitive].set_secondary_field(fact_type, fact[1], fact[2])
             else:
                 print("Unknown type, ignoring...")
           


  def transform():
      """Given some input data, applies the mappings and returns the transformed data"""
      pass



      # Apply to each line of data the known mappings

      # Create relevant Model for each 

      with open(self.filename,) as csv_file:
        reader = csv.DictReader(csv_file)

        # Throw the column values at the primitive mappings and save the result

# This needs to write different data out for different plugins.Maybe should be handled in 
# another class
