from GitShade.emerge.InitialNode import Position,Data,InitialNode,Style
from GitShade.emerge.Edges import Edge
import json
class gitShade:
    def __init__(self, graphRootNode):
        # set root node easier computation
        self._graphRootNode: str = graphRootNode
        # making nodes and edges of graph 
        self._gitShadeResult: dict[str, list[str]] = {}
        self._graphInitNodes: list[InitialNode] = []
        self._graphEdges: list[Edge] = []
        # array for all nodes
        self._allUniqueNodes: dict[str,str] = {}
        # used for assigning dynamic height and width for each folder (not using right now)
        self._graphAdjListFolders: dict[str,list[str]] = {}
        self._graphAdjListFiles: dict[str,list[str]] = {}
    
    def create_graphAdjListFolders(self):
        # traversing on folders and making its graph
        for node in self._graphInitNodes:
            if node.type == "group":
                if self._graphAdjListFolders.get(node.id) == None:
                    self._graphAdjListFolders[node.id] = []
                if self._graphAdjListFolders.get(node.parentNode) == None:
                    self._graphAdjListFolders[node.parentNode] = [] 
                self._graphAdjListFolders[node.parentNode].append(node.id)
        self._graphAdjListFolders["library"] = []
    
    def create_graphAdjListFilesInFolder(self):
        for node in self._graphInitNodes:
            if node.type == "group":
                for file in self._graphInitNodes:
                    if file.type == "custom" and file.parentNode == node.id:
                        if self._graphAdjListFiles.get(node.id) == None:
                            self._graphAdjListFiles[node.id] = []
                        self._graphAdjListFiles[node.id].append(file.id)

    def make_firstChildsVisible_orderBydependency(self):
        for initNode in self._graphInitNodes:
                if initNode.id == self._graphRootNode:
                    initNode.hidden = False
        
        # orderBydependency first group then its childs
        self._graphInitNodes.sort()
        
    def exportDataToFile(self):
        json_data_initNodes = json.dumps(gitShade.convertToDict(self._graphInitNodes))
        json_data_Edges = json.dumps(gitShade.convertToDict(self._graphEdges))
        json_data_info = json.dumps({ 'rootNode': self._graphRootNode })
        f = open("tmp/initNodes.json", "w")
        f.write(json_data_initNodes)
        f = open("tmp/initEdges.json","w")
        f.write(json_data_Edges)
        f = open("tmp/info.json","w")
        f.write(json_data_info)
        f.close()
    
    # converting emerge result to out dependency json structure {filename: ['dependency item1','dependency item2'...]}
    def structurize_basicFormat(self, _result:any):
        exampledict: dict[str,list[str]] = {}
        for item in _result.items():
            self._allUniqueNodes[item[0].split('.')[0]] = item[0]
        for item in _result.items():
            depd = str(item[1])
            depdList = []
            start = -1
            end = -1
            for ele in range(0,len(depd)):
                if depd[ele] == '[':
                    start = ele
                elif depd[ele] == ']':
                    end = ele
            depd = depd[start+1:end]
            depdList = depd.split(", ")
            for ele in range(0,len(depdList)) :
                depdList[ele] = depdList[ele][1:len(depdList[ele])-1]
                if self._allUniqueNodes.get(depdList[ele]) == None:
                    continue
                depdList[ele] = self._allUniqueNodes[depdList[ele]]
            self._gitShadeResult[item[0]] = depdList
    
    def structurize_desiredFormat(self, _rootNode: str):
        self._graphInitNodes.append(InitialNode("library",Position(),"group",Data(),None,"parent",Style(),True,False))
        # structuring json data for gitShade
        folderDict: dict[str,str] = {}
        EdgeIds = 1
        for item in self._gitShadeResult.items():
            keys: list = item[0].split("/")
            position = Position()
            data = Data("CaretDownFill",keys[len(keys)-1])
            boxList : list = []
            # making folder objects
            result = '/'.join(keys)
            parentNode = '/'.join(result.split('/')[:-2])
            result = '/'.join(result.split('/')[:-1])
            #folders till file name ex-> src/models/main.ts => src/models
            # src/assests/text/en.js
            # src/components/config/main.ts
            if parentNode == '':
                parentNode = None
            if folderDict.get(result) == None:
                boxNode: InitialNode = InitialNode(result,position,"group",Data("CaretDownFill",result),parentNode,"parent",Style(35,100),True,True)
                self._graphInitNodes.append(boxNode)
                folderDict[result] = 'ok'
            
            initial_node = InitialNode(item[0], position, "custom", data, result,"parent",Style(),True,False)
            self._graphInitNodes.append(initial_node)
            for edge in item[1]:
                if edge != "" and edge.startswith(_rootNode) == False and folderDict.get(edge) == None:
                    boxNode: InitialNode = InitialNode(edge,position,"custom",Data("CaretDownFill",edge),"library","parent",Style(),True,False)
                    self._graphInitNodes.append(boxNode)
                    folderDict[edge] = 'ok'
                    self._graphEdges.append(Edge(EdgeIds,item[0],edge))
                    EdgeIds = EdgeIds + 1
                else:
                    initialEdge = Edge(EdgeIds,item[0],edge)
                    self._graphEdges.append(initialEdge)
                    EdgeIds = EdgeIds + 1
        
        for initNode in self._graphInitNodes:
            if initNode.parentNode != None and folderDict.get(initNode.parentNode) == None:
                boxNode: InitialNode = InitialNode(initNode.parentNode,position,"group",Data("CaretDownFill",initNode.parentNode),'/'.join(initNode.parentNode.split("/")[:-1]),"parent",Style(35,100),True,True)
                self._graphInitNodes.append(boxNode)
                folderDict[initNode.parentNode] = 'ok'

    @staticmethod
    def convertToDict(ls: list):
        uniqueDict: dict[str,any] = {}
        for item in ls:
            if uniqueDict.get(item) == None:
                uniqueDict[item] = item
        result: list = []
        for item in uniqueDict.items():
            result.append(item[1].__dict__())
        
        return result
    
    def calculate_dimensions(self):
        self.create_graphAdjListFolders()
        self.create_graphAdjListFilesInFolder()
        #self.calculate_HeightWidh(self._graphRootNode)
        self.make_firstChildsVisible_orderBydependency()
        self.exportDataToFile()
        pass
    
    # below functions not using as of now
    def calculate_HeightWidh(self, rootNode: str):
        #base condition
        if len(self._graphAdjListFolders[rootNode]) == 0:
            return self.calculate_relativeHeight(rootNode)
        
        hht = 1
        wht = 1
        # recursive condition
        for folder in self._graphAdjListFolders[rootNode]:
            hwObj = self.calculate_HeightWidh(folder)
            hht = hht + hwObj["h"]
            wht = wht + hwObj["w"]
        
        return self.calculate_relativeHeight(rootNode,hht,wht)
        
    def calculate_relativeHeight(self, rootNode:str, hht=1, wht=1):
        try:
            totalChilds = len(self._graphAdjListFiles[rootNode])
            initNodeIndex: int
            for i in range(0,len(self._graphInitNodes)):
                if self._graphInitNodes[i].id == rootNode:
                    initNodeIndex = i
                    break
            self._graphInitNodes[initNodeIndex].style.height = hht + 10*totalChilds
            self._graphInitNodes[initNodeIndex].style.width = wht + 10*totalChilds
            return {"h":hht + 10*totalChilds,"w":wht + 10*totalChilds}
        except ValueError:
            print("That item does not exist")
            return {"h":10,"w":20}
