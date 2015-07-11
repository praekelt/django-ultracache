import uuid


class Tracker(dict):

    def get_new_key(self):
        key = uuid.uuid1()
        self[key] = []
        return key

tracker = Tracker()
