import yaml


class Config:
    def __init__(self, default_to=None):
        self.default_to = default_to
        self.data = {}
        self.load()

    def update(self, data):
        self.data.update(data)

    def load(self, path="config.yaml"):
        with open(path, "r", encoding="utf-8") as file:
            self.update(yaml.safe_load(file) or {})

    def save(self, path="config.yaml"):
        with open(path, "w", encoding="utf-8") as file:
            yaml.dump(self.data, file)
            
    def __getitem__(self, key):
        parts = key.split(".")
        data = self.data
        for part in parts:
            if part not in data:
                if self.default_to == "id":
                    return key
                elif self.default_to == "none":
                    return None
                else:
                    raise KeyError(key)
            data = data[part]
        return data
    
    def __setitem__(self, key, value):
        parts = key.split(".")
        data = self.data
        for part in parts[:-1]:
            if part not in data:
                data[part] = {}
            data = data[part]
        data[parts[-1]] = value

    def __delitem__(self, key):
        parts = key.split(".")
        data = self.data
        for part in parts[:-1]:
            data = data[part]
        del data[parts[-1]]
        
    def __contains__(self, key):
        parts = key.split(".")
        data = self.data
        for part in parts:
            if part not in data:
                return False
            data = data[part]
        return True

    def __repr__(self):
        return f"<Config data={self.data}>"
    
    def __str__(self):
        return str(self.data)
    
    def __iter__(self):
        return iter(self.data)
    
    def __len__(self):
        return len(self.data)
