# Croft 

Croft is programme to convert data into a website & visualisations. Based on a generic data model
or the basic features (which you stretch your data to fit into), plus confirmation and custom
extensions to adapt for some of the basic common features used in showing a dataset,
most usually for digital humanities. Example project types expected to work:

  - Participant/Event - Some people did some things at some points in time in some places (e.g. - 
  - Text/Event - Some texts were written at some point and then other things happened to them (e.g. - Vindolanda)
  - Place/Event - Some things happened at some places (e.g. historic gardens of Rome)
  - Participant/Event/Observation - Some things happened and some people had thoughts about that

As you can see, the core types are:
  
   - Participant 
   - Event
   - Place
   - Text
   - Document
   - Observation

most of which can then also have the other types relating.

In theory, this handles quite a lot of the basic data models created for DH projects, however be aware
that if you want a lot more complexity, you should probably start on your own project instead of trying
to fit it into this.

Based on Palladio.

## How it works

# Phase 1

Croft reads in your data and generates two outputs - Hugo markdown content and inferred data for visualisations

Data can be in a basic form as a single CSV, multiple CSV, JSON, etc.

# Phase 2 (optional)

Croft generate the visualisations as images or packages visualisation (?) within Jupyter (?)

### Phase 3

You need to then run Hugo to generate the site which turns the markdown content into HTML pages, generates the site structure (listings), and integrates
the visualisations.

### Phase 4 (optional)

Convert into a PWA so can be downloaded to a phone or tablet

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
  - Probably Mythical Generic Data Visualisation 

## Name

Was Named after Henry Flitcroft as croft but croft is too popular

Brid after Bridlington / Burlington / Palladio 
