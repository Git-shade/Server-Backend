class Edge:
    def __init__(self, id='', source="", target=""):
        self.id = id
        self.source = source
        self.target = target

    def __dict__(self):
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
        }