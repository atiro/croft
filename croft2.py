import sys
import json

sys.path.append(".")

from croft.datasource import DataSource
from croft.views.quarto import Quarto,Gallery,Table,Map,Data

with open('croft-config.json') as config_file:
    config = json.load(config_file)

# XXX Should have a seperate config reader to pass config around
datasource = DataSource(config)

print(datasource.data_files)

# XXX should loop through config to output views

# all this should come from config
table = Table(datasource = datasource, primitive="Event", slug="experience", link="Actor", name="Experiences", primary=True)
table.write("/tmp")

table2 = Table(datasource = datasource, primitive="Actor", slug="institution", name="Institutions")
table2.write("/tmp")

gal = Gallery(datasource = datasource, primitive='Actor', slug="institution", name="Institutions", primary=True)
gal.write("/tmp")

gal2 = Gallery(datasource = datasource, primitive='Event', slug="experience", name="Experiences")
gal2.write("/tmp")

q_map = Map(datasource = datasource, primitive='Actor', slug='institution', name='Map', primary=True)
q_map.write("/tmp")

# Write out datasette-lite file and sqlite DB of CSV
q_data = Data(datasource = datasource, primitive='Actor', slug='institution', name='Data', primary=True)
q_data.write("/tmp")

quarto_config = Quarto(keep_nav_names=True, config=config)
quarto_config.add_view(table)
#quarto_config.add_view(table2)
quarto_config.add_view(gal)
#quarto_config.add_view(gal2)
quarto_config.add_view(q_map)
quarto_config.add_view(q_data)

quarto_config.write("/tmp")
