# coding=utf-8
# Python 版本 : python3
# 日期 ： 2017-2-12
# 程序功能：
#       1. 给每个工程的资源增加工程前缀
#       2. 查找指定目录重名资源，自动改名，并修改在Json、ResourceConfig.xml内的引用
# 注意:
#       1. fnt 和对应的 png 是同时修改的
#       2. 注意 ResourceConfig.xml 的修改（看Log），因为在代码中可能显示引用到
#
# 用法：
#      1. 保证 SVN 目录干净整洁。（commit，revert,cleanUp）
#      2. 根据需要，使用 fun1()、fun2()、fun3()  
#      3. 程序结束后，会打开日志 logger.log

import os
import os.path
import sys
import json
import logging


class FileUtil:
    # 遍历所有文件和文件夹
    def enumFile(self, path, recursively):
        vecFile = []
        vecFolder = []
        if recursively:
            for folderPath, folderNames, fileNames in os.walk(path):
                vecFolder.append(folderPath)
                for name in fileNames:
                    filePath = os.path.join(folderPath, name)
                    vecFile.append(filePath)
        else:
            for name in os.listdir(path):
                filePath = os.path.join(path, name)
                if os.path.isfile(filePath):
                    vecFile.append(filePath)
                else:
                    vecFolder.append(filePath)
        return vecFolder, vecFile

    # 递归遍历路径下所有后缀为 .x 的文件
    def enumFileBySuffix(self, path, recursively, suffix):
        vecFolder, vecFile = self.enumFile(path, recursively)
        vecFile = [name for name in vecFile if name.endswith(suffix)]
        return vecFile

    def readFile(self, path):
        f = open(path, 'rt', encoding='utf-8', errors='ignore')
        str = f.read()
        f.close()
        return str

    def writeFile(self, path, str):
        f = open(path, 'wt', encoding='utf-8', errors='ignore')
        f.write(str)
        f.close()


class RenameInfo:
    def __init__(self):
        self.ext = ""  # .XXX
        self.oldName = ""  # 不带后缀
        self.oldFolder = ""  # xxx/
        self.newName = ""
        self.newFolder = ""


class Rename_Json:
    def __init__(self):
        self.dict = {}
        self.jsonDict = ""
        self.bModified = False
        self.projPath = ""
        self.jsonPath = ""

    def readJson(self):
        with open(self.jsonPath, 'rt', encoding='utf-8', errors='ignore') as f:
            self.jsonDict = json.load(f)

    def flushJson(self):
        if self.bModified:
            with open(self.jsonPath, 'wt', encoding='utf-8', errors='ignore') as f:
                json.dump(self.jsonDict, f, ensure_ascii=False, indent=2)

    def replace(self, projPath, jsonPath, vec_renameInfo):
        self.projPath = projPath
        self.jsonPath = jsonPath

        for fileInfo in vec_renameInfo:
            if not fileInfo.oldFolder.startswith(projPath):
                continue
            if self.jsonDict == "":
                self.readJson()
            self.SearchJsonImageValue(self.jsonDict, projPath, fileInfo)
        self.flushJson()

    def SearchJsonImageValue(self, jsonDict, projPath, fileInfo):
        value = jsonDict["widgetTree"]
        self._SearchJsonImageValue(value, projPath, fileInfo)

    def _SearchJsonImageValue(self, value, projPath, fileInfo):

        if not value or not "classname" in value:
            return
        classname = value["classname"]

        if classname == "Button" or classname == "TextButton":
            self.SearchButtonImageValue(value, projPath, fileInfo)
        elif classname == "CustomButton":
            self.SearchCustomButtonImageValue(value, projPath, fileInfo)
        elif classname == "CheckBox":
            self.SearchCheckBoxImageValue(value, projPath, fileInfo)
        elif classname == "ImageView":
            self.SearchImageViewImageValue(value, projPath, fileInfo)
        elif classname == "Label" or classname == "LabelArea":
            pass
        elif classname == "LabelAtlas":
            self.SearchLabelAtlasImageValue(value, projPath, fileInfo)
        elif classname == "LabelBMFont":
            self.SearchBMFontImageValue(value, projPath, fileInfo)
        elif classname == "LoadingBar":
            self.SearchLoadingBarImageValue(value, projPath, fileInfo)
        elif classname == "Slider":
            self.SearchSliderImageValue(value, projPath, fileInfo)
        elif classname == "TextField":
            self.SearchPanelImageValue(value, projPath, fileInfo)
        elif classname == "Layout" or classname == "Panel":
            self.SearchPanelImageValue(value, projPath, fileInfo)
        elif classname == "ListView":
            self.SearchPanelImageValue(value, projPath, fileInfo)
        elif classname == "PageView":
            self.SearchPanelImageValue(value, projPath, fileInfo)
        elif classname == "ScrollView":
            self.SearchPanelImageValue(value, projPath, fileInfo)
        elif classname == "QGButton":
            self.SearchQGButtonImageValue(value, projPath, fileInfo)

        if "children" in value:
            children = value["children"]
            for v in children:
                self._SearchJsonImageValue(v, projPath, fileInfo)

    def SearchButtonImageValue(self, value, projPath, fileInfo):
        if value and "options" in value:
            options = value["options"]
            strClassname = "Button"
            name = options["name"]

            if "normalData" in options:
                self.SearchImageValue(options["normalData"], projPath, fileInfo)
            if "pressedData" in options:
                self.SearchImageValue(options["pressedData"], projPath, fileInfo)
            if "disabledData" in options:
                self.SearchImageValue(options["disabledData"], projPath, fileInfo)

    def SearchCustomButtonImageValue(self, value, projPath, fileInfo):

        self.SearchButtonImageValue(value, projPath, fileInfo)

        if value and "options" in value:
            options = value["options"]
            strClassname = "CustomButton"
            name = options["name"]
            customProperty = options["customProperty"]
            if customProperty == "{":
                return

            jsonDict = json.loads(customProperty)

            if "HoverData" in jsonDict:
                hoverData = jsonDict["HoverData"]

                oldPath = os.path.join(fileInfo.oldFolder, fileInfo.oldName + fileInfo.ext)
                newPath = os.path.join(fileInfo.newFolder, fileInfo.newName + fileInfo.ext)
                resPath = os.path.join(projPath, "Resources")
                oldRelpath = os.path.relpath(oldPath, resPath)  # 获取相对路径
                newRelpath = os.path.relpath(newPath, resPath)  # 获取相对路径
                oldRelpath = oldRelpath.replace("\\","/")
            if hoverData == oldRelpath:
                self.bModified = True
                newRelpath = newRelpath.replace("\\","/")
                jsonDict["HoverData"] = newRelpath
                options["customProperty"] = json.dumps(jsonDict)

    def SearchQGButtonImageValue(self, value, projPath, fileInfo):
        self.SearchButtonImageValue(value, projPath, fileInfo)

        if value and "options" in value:
            options = value["options"]
            strClassname = "QGButton"
            name = options["name"]
            customProperty = options["customProperty"]
            if customProperty == "{":
                return
            jsonDict = json.loads(customProperty)

            oldPath = os.path.join(fileInfo.oldFolder, fileInfo.oldName + fileInfo.ext)
            newPath = os.path.join(fileInfo.newFolder, fileInfo.newName + fileInfo.ext)
            resPath = os.path.join(projPath, "Resources")
            oldRelpath = os.path.relpath(oldPath, resPath)  # 获取相对路径
            newRelpath = os.path.relpath(newPath, resPath)  # 获取相对路径
            oldRelpath = oldRelpath.replace("\\", "/")
            newRelpath = newRelpath.replace("\\", "/")

            bDictChanged = False
            if "TitleNormal" in jsonDict:
                TileNormal = jsonDict["TitleNormal"]
                if TileNormal == oldRelpath:
                    self.bModified = True
                    bDictChanged = True
                    jsonDict["TitleNormal"] = newRelpath
            if "TitleDisabled" in jsonDict:
                TitleDisabled = jsonDict["TitleDisabled"]
                if TitleDisabled == oldRelpath:
                    self.bModified = True
                    bDictChanged = True
                    jsonDict["TitleDisabled"] = newRelpath
            if "TitlePressed" in jsonDict:
                TitlePressed = jsonDict["TitlePressed"]
                if TitlePressed == oldRelpath:
                    self.bModified = True
                    bDictChanged = True
                    jsonDict["TitlePressed"] = newRelpath
            if bDictChanged:
                options["customProperty"] = json.dumps(jsonDict)



    def SearchCheckBoxImageValue(self, value, projPath, fileInfo):
        if value and "options" in value:
            options = value["options"]
            strClassname = "CheckBox"
            name = options["name"]

            if "backGroundBoxData" in options:
                self.SearchImageValue(options["backGroundBoxData"], projPath, fileInfo)
            if "backGroundBoxSelectedData" in options:
                self.SearchImageValue(options["backGroundBoxSelectedData"], projPath, fileInfo)
            if "frontCrossData" in options:
                self.SearchImageValue(options["frontCrossData"], projPath, fileInfo)
            if "backGroundBoxDisabledData" in options:
                self.SearchImageValue(options["backGroundBoxDisabledData"], projPath, fileInfo)
            if "frontCrossDisabledData" in options:
                self.SearchImageValue(options["frontCrossDisabledData"], projPath, fileInfo)

    def SearchImageViewImageValue(self, value, projPath, fileInfo):
        if value and "options" in value:
            options = value["options"]
            strClassname = "ImageView"
            name = options["name"]
        if "fileNameData" in options:
            self.SearchImageValue(options["fileNameData"], projPath, fileInfo)

    def SearchLabelAtlasImageValue(self, value, projPath, fileInfo):
        if value and "options" in value:
            options = value["options"]
            strClassname = "LabelAtlas"
            name = options["name"]
        if "charMapFileData" in options:
            self.SearchImageValue(options["charMapFileData"], projPath, fileInfo)

    def SearchBMFontImageValue(self, value, projPath, fileInfo):
        if value and "options" in value:
            options = value["options"]
            strClassname = "LabelBMFont"
            name = options["name"]
        if "fileNameData" in options:
            self.SearchImageValue(options["fileNameData"], projPath, fileInfo)

    def SearchLoadingBarImageValue(self, value, projPath, fileInfo):
        if value and "options" in value:
            options = value["options"]
            strClassname = "LoadingBar"
            name = options["name"]
        if "textureData" in options:
            self.SearchImageValue(options["textureData"], projPath, fileInfo)

    def SearchSliderImageValue(self, value, projPath, fileInfo):
        if value and "options" in value:
            options = value["options"]
            strClassname = "Slider"
            name = options["name"]
        if "ballNormalData" in options:
            self.SearchImageValue(options["ballNormalData"], projPath, fileInfo)
        if "ballPressedData" in options:
            self.SearchImageValue(options["ballPressedData"], projPath, fileInfo)
        if "ballDisabledData" in options:
            self.SearchImageValue(options["ballDisabledData"], projPath, fileInfo)
        if "progressBarData" in options:
            self.SearchImageValue(options["progressBarData"], projPath, fileInfo)

    def SearchPanelImageValue(self, value, projPath, fileInfo):
        if value and "options" in value:
            options = value["options"]
            strClassname = "Panel"
            name = options["name"]
        if "backGroundImageData" in options:
            self.SearchImageValue(options["backGroundImageData"], projPath, fileInfo)

    def SearchImageValue(self, value, projPath, fileInfo):
        if value and "path" in value:
            path = value["path"]
            oldPath = os.path.join(fileInfo.oldFolder, fileInfo.oldName + fileInfo.ext)
            newPath = os.path.join(fileInfo.newFolder, fileInfo.newName + fileInfo.ext)
            resPath = os.path.join(projPath, "Resources")
            oldRelpath = os.path.relpath(oldPath, resPath)  # 获取相对路径
            newRelpath = os.path.relpath(newPath, resPath)  # 获取相对路径

            oldRelpath = oldRelpath.replace("\\","/")
            if path == oldRelpath:
                self.bModified = True
                newRelpath = newRelpath.replace("\\", "/")
                value["path"] = newRelpath


class Rename_Fnt:
    def replace(self, projPath, vec_renameInfo):
        for fileInfo in vec_renameInfo:
            if fileInfo.ext == ".fnt" and fileInfo.oldFolder.startswith(projPath):
                pngPath = os.path.join(fileInfo.oldFolder, fileInfo.newName + ".png")
                if os.path.isfile(pngPath):
                    fileUtil = FileUtil()
                    fntStr = fileUtil.readFile(os.path.join(fileInfo.newFolder, fileInfo.newName + ".fnt"))
                    fntStr = fntStr.replace("file=\"" + fileInfo.oldName + ".png" + "\"",
                                            "file=\"" + fileInfo.newName + ".png" + "\"")
                    fileUtil.writeFile(os.path.join(fileInfo.newFolder, fileInfo.newName + ".fnt"), fntStr)


class Rename_Xml:
    def replace(self, projPath, xmlPath, vec_renameInfo):

        fileUtil = FileUtil()
        content = fileUtil.readFile(xmlPath)
        bModified = False
        xmlFolderPath = os.path.dirname(xmlPath)
        bLog = False
        for fileInfo in vec_renameInfo:
            if fileInfo.ext == ".png" and xmlFolderPath == fileInfo.oldFolder:
                if content.find(fileInfo.oldName + fileInfo.ext + "</FilterFile>") != -1:
                    content = content.replace(fileInfo.oldName + fileInfo.ext + "</FilterFile>",
                                              fileInfo.newName + fileInfo.ext + "</FilterFile>")
                    bModified = True
                    if not bLog:
                        logging.info("[ " + xmlPath + "]")
                        bLog = True
                    logging.info(fileInfo.oldName + fileInfo.ext + " -> " + fileInfo.newName + fileInfo.ext)

        if bModified:
            fileUtil.writeFile(xmlPath, content)


class UIProject:
    def __init__(self):
        self.folderPath = ""
        self.folderName = ""
        self.jsonPaths = []
        self.xmlPaths = []
        self.resources = []
        self.fileUtil = FileUtil()

    def isValidProject(self, path):
        if os.path.isdir(os.path.join(path, "Resources")) and os.path.isdir(os.path.join(path,"Json")):
            return True
        return False

    def initWithPath(self, path):
        self.folderName = os.path.split(path)[1]
        self.folderPath = path
        self.jsonPaths = self.fileUtil.enumFileBySuffix(os.path.join(path, "Json"), False, ".json")
        tmp, self.resources = self.fileUtil.enumFile(os.path.join(path, "Resources"), True)
        tmpXmlPaths = self.fileUtil.enumFileBySuffix(os.path.join(path, "Resources"), True, ".xml")
        for file in tmpXmlPaths:
            if os.path.split(file)[1].startswith("ResourceConfig"):
                self.xmlPaths.append(file)

    # 资源增加工程名前缀
    def renameResource(self):
        vector = []
        prefix = self.folderName + "_"
        for file in self.resources:
            if file.endswith(".png") or file.endswith(".fnt") and not file.startswith(prefix):
                renameInfo = RenameInfo()
                renameInfo.ext = os.path.splitext(os.path.basename(file))[1]
                renameInfo.oldName = os.path.splitext(os.path.basename(file))[0]
                renameInfo.newName = prefix + renameInfo.oldName
                renameInfo.oldFolder = renameInfo.newFolder = os.path.split(file)[0]

                vector.append(renameInfo)
        for i in vector:
            oldPath = os.path.join(i.oldFolder, i.oldName + i.ext)
            newPath = os.path.join(i.newFolder, i.newName + i.ext)
            os.rename(oldPath, newPath)  # 文件重命名
        # 修改引用
        self.replaceReference(vector)

    # 给定一个重名列表，替换跟本工程相关的资源
    def replaceReference(self, vec_renameInfo):
        for path in self.jsonPaths:
            renameJson = Rename_Json()
            renameJson.replace(self.folderPath, path, vec_renameInfo)

        for path in self.xmlPaths:
            renameXml = Rename_Xml()
            renameXml.replace(self.folderPath, path, vec_renameInfo)

        renameFnt = Rename_Fnt()
        renameFnt.replace(self.folderPath, vec_renameInfo)


class Checker:
    def check(self, vecPath):

        logging.info("Checker::check()")
        vecRenameInfo = []  # 返回值

        sameNameMap = {}
        # 同名的png
        for file in vecPath:
            if not file.endswith(".png"):
                continue
            ext = os.path.splitext(os.path.basename(file))[1]
            name = os.path.splitext(os.path.basename(file))[0]
            if name not in sameNameMap:
                sameNameMap[name] = []
            sameNameMap[name].append(file)

        # 去掉没有重名的
        for i in sameNameMap.copy():
            if len(sameNameMap[i]) < 2:
                sameNameMap.pop(i)
        logging.info("************ SameNameFile ************")
        for key, vec in sameNameMap.items():
            logging.info("[ " + key + "]")
            i = 0
            for v in vec:
                logging.info(v)
                renameInfo = RenameInfo()
                renameInfo.ext = os.path.splitext(os.path.basename(v))[1]
                renameInfo.oldName = os.path.splitext(os.path.basename(v))[0]
                renameInfo.newName = renameInfo.oldName + "_dp_" + str(i)
                renameInfo.oldFolder = renameInfo.newFolder = os.path.split(v)[0]

                vecRenameInfo.append(renameInfo)

                # 同名fnt
                fntPath = os.path.join(renameInfo.oldFolder, renameInfo.oldName + ".fnt")
                if os.path.isfile(fntPath):
                    renameInfo2 = RenameInfo()
                    renameInfo2.ext = ".fnt"
                    renameInfo2.oldName = renameInfo.oldName
                    renameInfo2.newName = renameInfo.newName
                    renameInfo2.oldFolder = renameInfo2.newFolder = renameInfo.oldFolder
                    vecRenameInfo.append(renameInfo2)

        return vecRenameInfo


# 功能1：传入单一工程目录，对Resource目录下资源增加UI工程前缀，并修改引用
# path example : Desktop/Art/Bag_pc
def fun1(path):
    UIProj = UIProject()
    UIProj.initWithPath(path)
    UIProj.renameResource()


# 功能2：传入UI工程总目录,批量执行 fun1
# path example : Desktop/Art
def fun2(path):
    fileUtil = FileUtil()
    vecFolders, vecFiles = fileUtil.enumFile(path, True)
    for folder in vecFolders:
        UIProj = UIProject()
        if UIProj.isValidProject(folder):
            fun1(folder)


# 功能3：传入UI工程总目录，找出所有重名资源(png,fnt)，并修改在 json,fnt，ResourceConfig.xml 中的引用
def fun3(path):
    vectorUIProj = []

    fileUtil = FileUtil()
    vecFolders, vecFiles = fileUtil.enumFile(path, True)
    # 遍历所有proj
    for folder in vecFolders:
        UIProj = UIProject()
        if UIProj.isValidProject(folder):
            UIProj.initWithPath(folder)
            vectorUIProj.append(UIProj)
    # 归并资源，检查重名
    vecMerge = []
    for ui in vectorUIProj:
        vecMerge += ui.resources

    checker = Checker()
    vecRename = checker.check(vecMerge)

    # 对重名文件，改名并修改引用
    for i in vecRename:
        oldPath = os.path.join(i.oldFolder, i.oldName + i.ext)
        newPath = os.path.join(i.newFolder, i.newName + i.ext)
        os.rename(oldPath, newPath)  # 文件重命名

    for ui in vectorUIProj:
        ui.replaceReference(vecRename)


if __name__ == "__main__":
    logging.basicConfig(filename='logger.log', level=logging.INFO)
    #fun1("D:\\tags\\jingji_proj\\ArtDir\\UI1280x720\Main")
    #fun2("D:\\tags\\jingji_proj\\ArtDir\\UI1280x720")
    #fun3("D:\\tags\\jingji_proj\\ArtDir\\UI1280x720")
    os.startfile("logger.log")