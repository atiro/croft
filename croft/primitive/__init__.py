
class Primitive():

    def __init__(self, link = 'Actor'):
        self.primary_fields = {}
        self.secondary_fields = {}
        self.link = link

    def set_primary_field(self, key, val):
        # XXX check if alredy set
        self.primary_fields[key] = val

    def set_secondary_field():
        # XXX check if alredy set
        self.secondary_fields[key] = val

    def get_primary_field(self, key):
        return self.primary_fields[key]

    def get_primary_fields(self):
        return self.primary_fields

    def get_secondary_fields(self):
        return self.secondary_fields

    def get_link_fields(self):
        return self.primary_fields[self.link]

class Actor(Primitive):

    # Should resitcit fields to those allowed

    def __init__(self):
        super().__init__()

class Event(Primitive):

    def __init__(self):
        super().__init__()

class Thing(Primitive):

    def __init__(self):
        super().__init__()

class Place(Primitive):

    def __init__(self):
        super().__init__()
