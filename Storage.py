import os
import json

class Store:
    def __init__(self, path="data.json"):
        self.path = path
        self.data = {}
        self.load()

    def load(self):
        if os.path.exists(self.path):
            with open(self.path, "r") as f:
                try:
                    self.data = json.load(f)
                except json.JSONDecodeError:
                    self.data = {}
        else:
            self.data = {}

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2)

    def set(self, key, value):
        self.data[key] = value
        self.save()

    def get(self, key, default=None):
        return self.data.get(key, default)

    def remove(self, key):
        if key in self.data:
            del self.data[key]
            self.save()

    def clear(self):
        self.data = {}
        self.save()