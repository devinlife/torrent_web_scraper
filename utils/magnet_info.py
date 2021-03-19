from datetime import datetime as dtime

class MagnetInfo():
    def __init__(self, title, magnet, matched_name):
        self.create_time = dtime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.title = title
        self.magnet = magnet
        self.matched_name = matched_name

    def __repr__(self):
        return "%s, %s, %s, %s" % (self.create_time, self.title, self.magnet, self.matched_name)

    def get_list(self):
        return [self.create_time, self.title, self.magnet, self.matched_name]
