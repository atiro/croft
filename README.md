# Croft 

  A quick way to record and show that something happened to someone
  at sometime and in someplace. 

Croft is a programme to quickly convert some factual data into a website view for wider dissemnination. 
Based around collections of statements each of which can have four primitive types (common to many research
projects data outputs) attached:

   - Actor  (Who)
   - Thing  (What)
   - Event  (When)
   - Place  (Where)

These all can have the following fields stored (one of which must act as a key to be group different data sources
together if your data is split into multiple CSV files)

   - Name
   - Description
   - Images[]
   - Websites[]
   - Location (Name, Description, Lat, Long)
   - DateTIme (When) (Name, Parsed)
   - Meta[] - Other fields (can be shown but cannot be used to form a data view)

Four secondary types can be attached to [name for ovreall thing]:

   - Text - Some information was created at the time and is known about
   - Document - Some information was created at the time and has a physical carrier
   - Observation - Some additional (textual) information was recorded (then or subsequently)
   - Measurement - Some additional (numeric) information was recorded (then or subsequently)

From this, you can configure different viewpoints to pull out the data for the view you need,
for example if you want to show:

  - Actor/Event - Some people did some things at some points in time in some places 
  - Event+Observation - Some texts were written at some point and then they were discovered later (e.g. - Vindolanda Tablets)
  - Place/Event/Actor - Some things happened at some places (e.g. historic gardens of Ancient Rome existed and had owners)
  - Actor/Event+Observation - Some things happened and some people had thoughts about that

all of which can then also have the other types relating to them.

Examples:
 
   Paintings made of Mount Vesuvisus

       Actor - Painter 
	   Thing - Painting

In theory, this handles quite a lot of basic data models created for DH projects, however be aware
that if you want this to be more complex, you should probably start on your own project instead of
trying to fit your data into this system. You could also consider using and extending OpenAtlas,
hich you will notice uses the same primitives (based on the CIDOC-CRM). 

Limitations:
  - Statements cannot be made about statements
  - 
Based on Palladio.

## How it works

# Step 1

Croft reads in your data and generates two outputs - Hugo markdown content and data for visualisations

Data can be in a basic form 
  - single CSV, 
  - multiple CSV (with common identifier)
  - YAML

# Step 2 (optional)

Croft generate visualisations either as static images or dynamic data visualisations (?) within Jupyter (?)

### Step 3

Running Hugo generates the site - this turns the markdown content into HTML pages, generates the site structure (listings), and
includes any visualisations.

### Step 4 (optional) - FUTURE

Convert into a PWA so can be downloaded to a phone or tablet and run as a standalone app.

## Plugins

Core (first 4 as per Palladio):
  - Gallery
  - Map
  - List
  - Network Visualisation
  - Blog

Planned:
  - Photo Wall
  - Event Timeline
  - Topic 
  - Mythical generic meaningful data visualisation interface

## Name

Named after Henry Flitcroft 
