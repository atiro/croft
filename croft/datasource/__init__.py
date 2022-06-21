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

  datasources = {}

  data_files = []

  def __init__(self, config):
      # Save mappings

      for source in config['source']:
        filename = source['filename']

        self.datasources[filename] = {}
        self.datasources[filename]['mappings'] = {}

        if "key" in source:
          self.datasources[filename]['key'] = source["key"]

        if "view" in source:
          self.datasources[filename]['view'] = source["view"]

        if "link" in source:
          self.datasources[filename]['link'] = source["link"]

## TODO could we assume there is always a link primitive and (possibly) a single second primitve ?

        for mapping in source['mapping']:
          user_field, primitive,*alt_names = mapping
          alt_name = None
#          ds_fields.append(user_field)
#          ds_mappings.append(mapping)

          if "/" in primitive:
            primitive_type,primitive_field = primitive.split('/')
          else:
            primitive_type,primitive_field = primitive.split("::")

          if len(alt_names) > 0:
            alt_name = alt_names[0]

          self.datasources[filename]['mappings'][user_field] = {}
          self.datasources[filename]['mappings'][user_field]['primitive_type'] = primitive_type
          self.datasources[filename]['mappings'][user_field]['primitive_field'] = primitive_field
          self.datasources[filename]['mappings'][user_field]['alt_name'] = alt_name
          self.datasources[filename]['mappings'][user_field]['link'] = True if (source["link"] == user_field) else False

        # Now we parse the data. Really we should do this in a sub class or this class should be called
        # Statements/Graph which creates a datasource per file.

        self.read_datasource(filename)

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
          print("New row")
          for col in row:
              if col != None and len(col) > 0:
                primitive, field = self.map_column(filename, col)
              else:
                print("CSV file contains extra column on line X, ignoring")
                continue

              if primitive == None:
                  continue

              if self.datasources[filename]['mappings'][col]['link']:
                link_id = row[col]
                link_primitive = primitive

              facts.append([primitive, field, row[col]])

          # If we've not seen anything for this statement before, initilise it

          if link_id not in self.statements:
             print(f"Creating link id for {link_id}")
             self.statements[link_id] = {}
             self.statements[link_id]['Actor'] = Actor()
             self.statements[link_id]['Place'] = Place()
             self.statements[link_id]['Thing'] = Thing()
             self.statements[link_id]['Event'] = Event()
             self.statements[link_id]['_filename_'] = sanitize_filename(link_id).replace(" ", "-").lower()
             self.statements[link_id]['_title_'] = link_id
          else:
              print(f"Link id {link_id} already exists")

           # Now add all the associated facts for this statement

          for fact in facts:
             fact_type = fact[0]
             print(f"Setting fact {fact_type} {fact[1]} {fact[2]}")
             # Can use match/case when python 3.10 widely used...
             if (fact_type == "Actor") or (fact_type == "Event") or (fact_type == "Place") or (fact_type == "Thing"):
                    self.statements[link_id][fact_type].set_primary_field(fact[1], fact[2])
             elif ((fact_type == "Measurement") or (fact_type == "Observation") or (fact_type == "Text") or (fact_type == "Document")):
                    self.statements[link_id][link_primitive].set_secondary_field(fact_type, fact[1], fact[2])
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
