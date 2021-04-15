# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TOMsExport
                                 A QGIS plugin
 Export of TOMs geometry data
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2019-11-01
        git sha              : $Format:%H$
        copyright            : (C) 2019 by TH
        email                : th"mhtc.co.uk
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""


import os.path, math
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

# from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from qgis.PyQt.QtGui import (QIcon, QStandardItemModel, QStandardItem
                             )
from qgis.PyQt.QtWidgets import (
    QAction,
    QWidget,
    QMessageBox,
    QDialog,
    QVBoxLayout, QCheckBox, QListView, QAbstractItemView, QFormLayout, QDialogButtonBox, QLabel, QGroupBox
)

from qgis.PyQt.QtCore import (
    QObject,
    QTimer,
    pyqtSignal,
    QSettings, QTranslator, qVersion, QCoreApplication, Qt, QModelIndex
)

from qgis.core import (
    Qgis,
    QgsExpressionContextUtils,
    QgsExpression,
    QgsFeatureRequest,
    # QgsMapLayerRegistry,
    QgsMessageLog, QgsFeature, QgsGeometry,
    QgsTransaction, QgsTransactionGroup,
    QgsProject,
    QgsVectorFileWriter,
    QgsApplication,
    QgsVectorLayer,
    QgsFields, QgsDataSourceUri, QgsWkbTypes, QgsMapLayerType, NULL
)

from qgis.gui import QgsFileWidget, QgisInterface
from qgis.utils import iface

# Initialize Qt resources from file resources.py
from resources import *
# Import the code for the dialog
from TOMsExport_dialog import TOMsExportDialog

import os.path
import time
import datetime

from TOMs.core.TOMsGeometryElement import ElementGeometryFactory
from TOMs.core.TOMsMessageLog import TOMsMessageLog
from TOMs.generateGeometryUtils import generateGeometryUtils
from TOMs.restrictionTypeUtilsClass import RestrictionTypeUtilsMixin, TOMsLayers, TOMsConfigFile
from TOMsExport.checkableMapLayerList import checkableMapLayerListCtrl, checkableMapLayerList
#from .restrictionTypeUtilsClass import RestrictionTypeUtilsMixin, TOMsLayers, TOMsConfigFile

class TOMsExport:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'TOMsExport_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&TOMsExport')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

        self.closeTOMs = False

    def tr(self, message):
        """Get the translation for a string using Qt translation API.
        """
        return QCoreApplication.translate('TOMsExport', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/TOMsExport/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'TOMs Export'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&TOMsExport'),
                action)
            self.iface.removeToolBarIcon(action)


    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started

        self.TOMsConfigFileObject = TOMsConfigFile(self.iface)
        self.TOMsConfigFileObject.TOMsConfigFileNotFound.connect(self.setCloseTOMsFlag)
        self.TOMsConfigFileObject.initialiseTOMsConfigFile()

        utils = TOMsExportUtils(self.iface, self.TOMsConfigFileObject)

        if self.first_start == True:
            self.first_start = False

        self.tableNames = TOMsLayers(self.iface)
        #self.tableNames = setupTableNames(self.iface)
        self.tableNames.TOMsLayersNotFound.connect(self.setCloseTOMsFlag)
        #self.TOMsExportLayerList = self.tableNames.getLayers()
        #requiredFields = self.tableNames.getRequiredFields()

        self.tableNames.TOMsLayersNotFound.connect(self.setCloseTOMsFlag)
        self.tableNames.getLayers(self.TOMsConfigFileObject)

        if self.closeTOMs:
            QMessageBox.information(self.iface.mainWindow(), "ERROR", ("Unable to start TOMs ..."))
            return

        #self.TOMsExportLayerList = utils.getTOMsExportLayerList()  # not required as list comes from dialog
        # TODO: Check that export layers are present ...

        self.setupUi()

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        # TODO: Make sure that there is a valid file location

        if result:

            # Open geopackage

            canvas = self.iface.mapCanvas()
            layer = canvas.currentLayer()

            fileName = self.fileNameWidget.filePath()
            # QMessageBox.information(self.iface.mainWindow(), "Message", ("Filename is ..." + str(fileName)))
            TOMsMessageLog.logMessage("Filename is ..." + str(fileName), level=Qgis.Info)

            # Get list of all the layers that are required within the Geopackage

            layerItemsList = self.layerList.getSelectedLayers()
            for currLayerItem in layerItemsList:
                TOMsMessageLog.logMessage("Processing {} ...".format(currLayerItem.text()), level=Qgis.Warning)

                currLayer = QgsProject.instance().mapLayersByName(currLayerItem.text())[0]

                outputLayersList = utils.processLayer(currLayer)
                if outputLayersList:
                    #status = utils.saveOutputLayers(outputlayersList, fileName)
                    for newLayerName, newLayer in outputLayersList:
                        utils.saveLayerToGpkg(newLayer, fileName)

                        newLayerA = QgsVectorLayer(fileName + "|layername=" + newLayerName, newLayerName,
                                                  "ogr")
                        QgsProject.instance().addMapLayer(newLayerA)

            TOMsMessageLog.logMessage("******** FINSIHED EXPORT ********", level=Qgis.Warning)

            #self.dlg.close()

    def setupUi(self):

        self.dlg = QDialog()
        self.dlg.setWindowTitle("TOMs Export")
        self.dlg.setWindowModality(Qt.ApplicationModal)

        self.generalLayout = QVBoxLayout()

        layerGroup = QGroupBox("Choose layers to export")

        # add map layer list
        self.layerList = checkableMapLayerList()
        vbox1 = QVBoxLayout()
        vbox1.addWidget(self.layerList)
        layerGroup.setLayout(vbox1)
        self.generalLayout.addWidget(layerGroup)

        # add file chooser
        outputGroup = QGroupBox("Choose output file")
        self.fileNameWidget = QgsFileWidget()
        self.fileNameWidget.setStorageMode(QgsFileWidget.SaveFile)
        self.fileNameWidget.setFilter("Geopackage (*.gpkg);;JPEG (*.jpg *.jpeg);;TIFF (*.tif)")
        self.fileNameWidget.setSelectedFilter("Geopackage (*.gpkg)")
        vbox2 = QVBoxLayout()
        vbox2.addWidget(self.fileNameWidget)
        outputGroup.setLayout(vbox2)
        self.generalLayout.addWidget(outputGroup)

        # add buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok
                                          | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.dlg.accept)
        self.buttonBox.rejected.connect(self.dlg.reject)
        self.generalLayout.addWidget(self.buttonBox)

        self.dlg.setLayout(self.generalLayout)
        checkableMapLayerListCtrl(self.layerList)

    def setCloseTOMsFlag(self):
        self.closeTOMs = True

class TOMsExportUtils():

    def __init__(self, iface, configFileObject):
        self.iface = iface
        self.configFileObject = configFileObject

        self.includeLookupValues = False
        if self.getIncludeLookupValues():
            self.includeLookupValues = True
        TOMsMessageLog.logMessage(
                "In TOMsExportUtils.init. includeLookupValue is {}".format(self.includeLookupValues),
                level=Qgis.Warning)

    def getTOMsExportLayerList(self):
        layers = self.configFileObject.getTOMsConfigElement('TOMsExport', 'LayersToExport')
        if layers:
            exportLayerList = layers.split('\n')
            return exportLayerList
        return None

    def getOnlyCurrentFeatures(self):
        value = self.configFileObject.getTOMsConfigElement('TOMsExport', 'GetOnlyCurrentFeatures')
        if value == 'True':
            return True
        return False

    def exportBaysAsPolygons(self):
        value = self.configFileObject.getTOMsConfigElement('TOMsExport', 'BaysAsPolygons')
        if value == 'True':
            return True
        return False

    def getResetNameValue(self):
        value = self.configFileObject.getTOMsConfigElement('TOMsExport', 'ResetNameValue')
        if value:
            return value
        return None

    def getIncludeLookupValues(self):
        value = self.configFileObject.getTOMsConfigElement('TOMsExport', 'IncludeLookupValues')
        if value:
            return value
        return False

    def getFieldsForExportLayer(self, layerName):
        configName = layerName + '.Fields'
        fields = self.configFileObject.getTOMsConfigElement('TOMsExport', configName)
        if fields:
            layerFieldList = fields.split('\n')
            return layerFieldList

        return None

    def processLayer(self, currLayer):

        TOMsMessageLog.logMessage("In processLayer - Considering layer: ".format(currLayer.name()), level=Qgis.Warning)

        # get the fields to include
        listFieldsToInclude = self.getFieldsForExportLayer(currLayer.name())
        TOMsMessageLog.logMessage("In processLayer - fields are {}".format(listFieldsToInclude), level=Qgis.Warning)

        if not listFieldsToInclude:
            reply = QMessageBox.information(None, "Information", "No fields found for layer {}".format(currLayer.name()), QMessageBox.Ok)
            return None  # no details to add

        # take string and turn into fields
        fieldsToInclude = self.setFieldsForTOMsExportLayer(currLayer, listFieldsToInclude)

        # decide whether or not to use only current restrictions.
        if self.isThisTOMsLayerUsingCurrentFeatures(currLayer) == True:
            text = '"OpenDate" IS NOT NULL AND "CloseDate" IS NULL'
            exp = QgsExpression(text)
            request = QgsFeatureRequest(exp)
            restrictionIterator = currLayer.getFeatures(request)
        else:
            restrictionIterator = currLayer.getFeatures()

        layerWkbType = currLayer.wkbType()
        outputLayersList = []
        #restrictionList = currLayer.getFeatures(request)

        for currRestriction in restrictionIterator:
            TOMsMessageLog.logMessage("In processLayer - geomID: {}".format(currRestriction.attribute("GeometryID")),
                                     level=Qgis.Warning)

            # deal with Bays as polygons ...
            if currLayer.name() == "Bays":
                if self.exportBaysAsPolygons() == True:
                    currGeomShapeID = currRestriction.attribute("GeomShapeID")
                    if currGeomShapeID < 20:
                        TOMsMessageLog.logMessage(
                            "In processLayer - Changing geomShapeID from {} to {}".format(currGeomShapeID, currGeomShapeID + 20),
                            level=Qgis.Warning)

                        currRestriction[currRestriction.fields().indexFromName("GeomShapeID")] = currGeomShapeID + 20
                        #currRestriction.setAttribute("GeomShapeID", currGeomShapeID+20)

            restrictionGeometryWkbType = self.getRestrictionGeometryWkbType(currRestriction, layerWkbType)
            # check that we have a layer created
            outputLayerName = '{currLayerName}_{ext}'.format(currLayerName=currLayer.name(), ext=QgsWkbTypes.displayString(restrictionGeometryWkbType))
            # check to see whether or not this layer has been created already
            #print ('---- layerName: {}'.format(outputLayerName))
            try:
                outputLayer = dict(outputLayersList)[outputLayerName]
            except KeyError as e:
                outputLayer = self.prepareNewLayer (currLayer, outputLayerName, restrictionGeometryWkbType, fieldsToInclude)

                #print('Fields in output: {}'.format(len(outputLayer.fields())))

                outputLayersList.append((outputLayerName, outputLayer))
                #print('- Appending --- layerName: {}'.format(outputLayerName))
                #outputLayer.startEditing()

            result = self.processRestriction(currLayer, currRestriction, outputLayer)
            if result == False:
                reply = QMessageBox.information(None, "Information", "failure to write to layer.", QMessageBox.Ok)
                TOMsMessageLog.logMessage(
                    "In processLayer: failure to write to layer ...",
                    level=Qgis.Info)
                break

        for newLayerName, newLayer in outputLayersList:
            newLayer.reload()
            newLayer.updateFields()
            newLayer.updateExtents()
            TOMsMessageLog.logMessage("In processLayer: layer: {}, count: {}".format(newLayerName, newLayer.featureCount()),
                                     level=Qgis.Info)
            QgsProject.instance().addMapLayer(newLayer)
            #canvas.setLayers([newLayer])

        return outputLayersList

    def saveLayerToGpkg(self, newLayer, fileName):

        #for newLayerName, newLayer in outputLayersList:
        write_result = False

        TOMsMessageLog.logMessage("In saveLayerToGpkg - {}, count:{}".format(newLayer.name(), newLayer.featureCount()), level=Qgis.Info)
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.layerName = newLayer.name()
        options.driverName = "GPKG"
        #options.sourceCRS = newLayer.crs()
        options.destCRS = newLayer.crs()
        #options.editionCapabilities = QgsVectorFileWriter.CanAddNewLayer

        geometry_column = 'geom'
        newURI = newLayer.dataProvider().uri()
        newURI.setDatabase(fileName)
        newURI.setDataSource('', newLayer.name(), geometry_column)
        newURI.setSrid = newLayer.crs()
        newURI.setTable = newLayer.name()
        #newURI.setKeyColumn = newLayer.primaryKeyAttributes()[0]
        options.datasourceOptions = [newURI.uri()]

        # check to see if file exists
        if os.path.isfile(fileName):
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer

        """ This approach is depreciated. 
            New approach is to use .create() function to create writer and then addFeatures(). 
            However, I can't quite make it work. There is something with addfeatures that doesn't work ... """
        # TODO: check that using dataprovider when using addFeatures ...

        write_result, error_message = QgsVectorFileWriter.writeAsVectorFormat(
            newLayer,
            fileName,
            options)

        if write_result != QgsVectorFileWriter.NoError:
            TOMsMessageLog.logMessage("Error: {errorNr} on {layer}: {txt}".format(errorNr=write_result, layer=newLayerName, txt=error_message), level=Qgis.Info)
            #print(currLayer.name(), self.writer)

        return write_result

    def isThisTOMsLayerUsingCurrentFeatures(self, currLayer):
        # Decide whether or not this is a TOMs layer.
        # Look for "OpenDate" and check whether or not there are values set

        if self.getOnlyCurrentFeatures() == False:
            return False

        isTOMsLayer = False
        currFields = currLayer.fields()

        for field in currFields:
            if field.name() == "OpenDate":
                exp = QgsExpression('OpenDate IS NOT NULL')
                request = QgsFeatureRequest(exp)
                relevantFeaturesIterator = currLayer.getFeatures(request)
                # https://stackoverflow.com/questions/3345785/getting-number-of-elements-in-an-iterator-in-python
                sumRelevantFeatures = sum(1 for _ in relevantFeaturesIterator)
                if sumRelevantFeatures > 0:
                    isTOMsLayer = True

        return isTOMsLayer

    def getRestrictionGeometryWkbType(self, currRestriction, layerGeomWkbType):
        # decide geometry type required based on layer geometry and GeomShapeID

        restrictionGeometryWkbType = layerGeomWkbType

        if layerGeomWkbType == QgsWkbTypes.LineString or layerGeomWkbType == QgsWkbTypes.MultiLineString:
            restrictionGeometryWkbType = QgsWkbTypes.MultiLineString

            # deal with non-TOMs layers
            try:
                geomShape = currRestriction.attribute("GeomShapeID")
            except KeyError as e:
                TOMsMessageLog.logMessage("In TOMsGeometryElement.init: GeomShapeID not present {}".format(e),
                                          level=Qgis.Info)
                return layerGeomWkbType

            if geomShape > 20:
                restrictionGeometryWkbType = QgsWkbTypes.MultiPolygon

        return restrictionGeometryWkbType

    def setFieldsForTOMsExportLayer(self, currLayer, reqFields):

        currFields = currLayer.fields()
        newFields = QgsFields()

        relationsForCurrLayer = self.getRelationsForCurrLayer(currLayer)

        """ Loop through all the fields in currLayer and add as appropriate"""
        for field in currFields:
            if field.name() in reqFields:
                # Check whether or not this is a lookup field
                if self.includeLookupValues:
                    fieldType = self.getLookupFieldType(currFields.indexFromName(field.name()), relationsForCurrLayer)
                    if fieldType:
                        field.setType(fieldType)
                        TOMsMessageLog.logMessage("Setting  {} to {}".format(field.name(), fieldType), level=Qgis.Warning)
                status = newFields.append(field)
                if status == False:
                    TOMsMessageLog.logMessage("Error adding " + field.name(), level=Qgis.Warning)

        return newFields

    def getLookupFieldType(self, idxField, relationsForCurrLayer):
        # returns field details with datatype of lookup

        fieldType = None

        if len(relationsForCurrLayer) > 0:
            # check to see if field has a lookup
            for relation in relationsForCurrLayer:
                if relation.referencingFields()[0] == idxField:
                    TOMsMessageLog.logMessage(
                        "In getLookupFieldType: checking field details for idx {} on {}".format(
                            idxField, relation.referencingLayer().name()),
                        level=Qgis.Warning)
                    try:
                        lookupField = relation.referencedLayer().fields().field("Description")  # this is the field that we will use for export
                        # change data type for this field
                        fieldType = lookupField.type()
                    except KeyError as e:
                        TOMsMessageLog.logMessage(
                            "In setFieldsForTOMsExportLayer: lookup field error for {}: {}. {}".format(
                                idxField, relation.referencedLayer().name(), e),
                            level=Qgis.Warning)
                        relationsForReferencedLayer = self.getRelationsForCurrLayer(relation.referencedLayer())
                        """if len(relationsForReferencedLayer) == 1:  # only allow further check for simple (one field) relations
                            fieldType = self.getLookupFieldType(relation.referencedFields()[0], relationsForReferencedLayer)"""

                        # need to choose the relation for the field we are considering ...
                        for newRelation in relationsForReferencedLayer:
                            if newRelation.referencingFields()[0] == relation.referencedFields()[0]:
                                fieldType = self.getLookupFieldType(newRelation.referencingFields()[0], relationsForReferencedLayer)
                                break

                    break

        return fieldType

    def prepareNewLayer(self, currLayer, newLayerName, geomWkbType, reqFields):

        currCrs = currLayer.crs().authid()
        #print ('---------- layer CRS: {}'.format(currCrs))
        TOMsMessageLog.logMessage('---------- layer CRS: {}'.format(currCrs), level=Qgis.Info)
        #currCrs = 'EPSG:27700'

        """newLayer = QgsVectorLayer("{type}?={crs}".format(type=geomType,
                                                         crs='EPSG:27700'), newLayerName, "memory")"""
        newLayer = QgsVectorLayer("{type}?crs={crs}".format(type=QgsWkbTypes.displayString(geomWkbType), crs=currCrs),
                                  newLayerName,
                                  "memory")

        #newFields = self.setFieldsForTOMsExportLayer(currLayer, reqFields)
        newLayer.dataProvider().addAttributes(reqFields)
        #newLayer.reload()
        newLayer.updateFields()

        return newLayer

    def processRestriction(self, currLayer, currRestriction, newLayer):

        currFields = currRestriction.fields()
        fieldsToInclude = newLayer.fields()
        newFeature = QgsFeature(fieldsToInclude)

        TOMsMessageLog.logMessage('*** Nr new fields: {}; curr fields {}'.format(len(fieldsToInclude), len(currFields)),
                                         level=Qgis.Info)
        geomShapeField = False

        relationsForCurrLayer = self.getRelationsForCurrLayer(currLayer)  # could move this up a level ...

        for field in fieldsToInclude:
            TOMsMessageLog.logMessage("Checking field: {}".format(field.name()),
                                      level=Qgis.Info)
            # fields for lookups will not match due to differences in data type
            TOMsMessageLog.logMessage("Adding " + field.name() + ":" + str(currRestriction.attribute(field.name())),
                                         level=Qgis.Info)

            # TODO: deal with lookup values ...
            fieldValue = self.getFieldValues(currRestriction, field, relationsForCurrLayer)

            # if "name" field - and this is initial export, change to provided value
            if field.name() == 'CreatePerson' or field.name() == 'LastUpdatePerson':
                fieldValue = self.getResetNameValue()

            #newFeature.setAttribute(field.name(), currRestriction.attribute(field.name()))
            newFeature.setAttribute(field.name(), fieldValue)

            if field.name() == 'GeomShapeID':
                geomShapeField = True

        #newGeom = currRestriction.geometry()  # use this for testing

        currGeomWkbType = currRestriction.geometry().type()

        if geomShapeField == True:
            if currGeomWkbType == QgsWkbTypes.LineGeometry:
                newGeom = ElementGeometryFactory.getElementGeometry(currRestriction)
                newFeature.setGeometry(newGeom)
            else:
                newFeature.setGeometry(currRestriction.geometry())
        else:
            newFeature.setGeometry(currRestriction.geometry())

        result = newLayer.dataProvider().addFeature(newFeature)
        if result == False:
            TOMsMessageLog.logMessage("In processRestriction. Error: {}".format(newLayer.dataProvider().errors()),
                                      level=Qgis.Warning)
        return result

    def getVectorLayers(self, layers):
        vectorLayers = []
        for name, layerObj in layers.items():
            # print (name, layerObj)
            if layerObj.type() == QgsMapLayerType.VectorLayer:
                vectorLayers.append(layerObj)
        return vectorLayers

    def getRelationsForCurrLayer(self, currLayer):

        vectorLayers = self.getVectorLayers(QgsProject.instance().mapLayers())
        relations = QgsProject.instance().relationManager().discoverRelations([], vectorLayers)

        relationsForCurrLayer = []

        for relation in relations:
            if relation.referencingLayer() == currLayer:
                relationsForCurrLayer.append(relation)
                #relationsForCurrLayer.append(relation.referencingLayer(), relation.referencingFields()[0])

        return relationsForCurrLayer

    def getFieldValues(self, currRestriction, field, relationsForCurrLayer):

        TOMsMessageLog.logMessage(
            "In getFieldValues ... ".format(field.name()),
            level=Qgis.Info)

        fieldValue = currRestriction.attribute(field.name())

        # deal with lookups
        if self.includeLookupValues:

            if len(relationsForCurrLayer) > 0:

                # check to see if field has a lookup
                for relation in relationsForCurrLayer:
                    if relation.referencingFields()[0] == currRestriction.fieldNameIndex(field.name()):
                        fieldValue = self.getLookupDescription(relation, currRestriction)
                        break  # assume only one field

        return fieldValue

    def getLookupDescription(self, relation, currRestriction):
        # possibly recursive ...

        TOMsMessageLog.logMessage("In getLookupDescription (1). Checking {} for field {}. current value: {}".format(relation.referencingLayer().name(), \
            currRestriction.fields().field(relation.referencingFields()[0]).name(), \
            currRestriction.attribute(relation.referencingFields()[0])), level=Qgis.Warning)

        fieldValue = None

        # check to see if the initial value is actually NULL

        if currRestriction.attribute(relation.referencingFields()[0]) != NULL:

            TOMsMessageLog.logMessage("In getLookupDescription (2). Checking {} in {} ... ".format(relation.getReferencedFeature(currRestriction).fields().field(relation.referencedFields()[0]).name(), \
                                                                      relation.referencedLayer().name()), level=Qgis.Warning)

            try:
                fieldValue = relation.getReferencedFeature(currRestriction).attribute("Description")
            except KeyError as e:

                TOMsMessageLog.logMessage("In getLookupDescription: error on {}. Checking next level ...".format(relation.referencedLayer().name()), level=Qgis.Warning)

                # check to see whether or not there are any further relations that might allow the lookup ...
                relationsForReferencedLayer = self.getRelationsForCurrLayer(relation.referencedLayer())

                # need to choose the relation for the field we are considering ...
                for newRelation in relationsForReferencedLayer:
                    if newRelation.referencingFields()[0] == relation.referencedFields()[0]:

                        checkRestriction = relation.getReferencedFeature(currRestriction)

                        TOMsMessageLog.logMessage("In getLookupDescription (3). Found relation for {} in {} ... {} on {}".format(
                            relation.getReferencedFeature(currRestriction).fields().field(relation.referencedFields()[0]).name(), \
                            relation.referencedLayer().name(), \
                            newRelation.getReferencedFeature(checkRestriction).fields().field(newRelation.referencedFields()[0]).name(), \
                            newRelation.referencedLayer().name() \
                            ), level=Qgis.Warning)

                        if len (checkRestriction.fields()) > 0:
                            TOMsMessageLog.logMessage("In getLookupDescription (4): Checking {}: {}".format(newRelation.referencedLayer().name(), \
                                                               newRelation.getReferencedFeature(checkRestriction).attribute(relation.referencedFields()[0])), level=Qgis.Warning)
                            fieldValue = self.getLookupDescription(newRelation, checkRestriction)

        return fieldValue


class checkableMapLayerListCtrl:
    """PyCalc Controller class."""
    def __init__(self, view):
        """Controller initializer."""
        self._view = view
        # Connect signals and slots
        self._connectSignals()

    def _connectSignals(self):
        """Connect signals and slots."""
        self._view.select_all_cb.clicked.connect(lambda: self._view.selectAllCheckChanged(self._view.select_all_cb, self._view.model))
        self._view.view.clicked.connect(lambda: self._view.listviewCheckChanged(self._view.model, self._view.select_all_cb))
        self._view.view.clicked[QModelIndex].connect(self._view.updateSelectedLayers)

class checkableMapLayerList(QWidget):

    # create a checkable list of the map layers

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        layerList = QgsProject.instance().layerTreeRoot().findLayers()
        self.iface = iface

        """for layer in layerList:
            print(layer.name())"""

        self.selectedLayers = []

        layout = QVBoxLayout()
        self.model = QStandardItemModel()

        self.select_all_cb = QCheckBox('Check All')
        self.select_all_cb.setChecked(True)
        self.select_all_cb.setStyleSheet('margin-left: 5px; font: bold')
        #self.select_all_cb.stateChanged.connect(lambda: selectAllCheckChanged(select_all_cb, model))
        layout.addWidget(self.select_all_cb)

        self.view = QListView()
        self.view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.view.setSelectionMode(QAbstractItemView.NoSelection)
        self.view.setSelectionRectVisible(False)

        for layer in layerList:
            item = QStandardItem(layer.name())
            # item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            # item.setData(QVariant(Qt.Checked), Qt.CheckStateRole)
            item.setCheckable(True)
            item.setSelectable(False)
            item.setCheckState(QtCore.Qt.Checked)
            self.model.appendRow(item)
            self.selectedLayers.append(item)

        self.view.setModel(self.model)

        #view.clicked.connect(lambda: listviewCheckChanged(item, model, select_all_cb))

        layout.addWidget(self.view)

        self.setLayout(layout)
        """if parent:
            parent.setLayout(layout)
        else:
            window = QWidget()
            window.setLayout(layout)"""
        #window.show()

    def selectAllCheckChanged(self, select_all_cb, model):
        TOMsMessageLog.logMessage("IN selectAllCheckChanged",
                                 level=Qgis.Info)
        for index in range(model.rowCount()):
            item = model.item(index)
            if item.isCheckable():
                if select_all_cb.isChecked():
                    item.setCheckState(QtCore.Qt.Checked)
                    self.selectedLayers.append(item)
                else:
                    item.setCheckState(QtCore.Qt.Unchecked)
                    self.selectedLayers.remove(item)

        TOMsMessageLog.logMessage("IN selectAllCheckChanged: len list {}".format(len(self.selectedLayers)),
                                 level=Qgis.Info)

    def listviewCheckChanged(self, model, select_all_cb):
        ''' updates the select all checkbox based on the listview '''
        # model = self.listview.model()
        TOMsMessageLog.logMessage("IN listviewCheckChanged",
                                 level=Qgis.Info)
        items = [model.item(index) for index in range(model.rowCount())]
        if all(item.checkState() == QtCore.Qt.Checked for item in items):
            select_all_cb.setTristate(False)
            select_all_cb.setCheckState(QtCore.Qt.Checked)
        elif any(item.checkState() == QtCore.Qt.Checked for item in items):
            select_all_cb.setTristate(True)
            select_all_cb.setCheckState(QtCore.Qt.PartiallyChecked)
        else:
            select_all_cb.setTristate(False)
            select_all_cb.setCheckState(QtCore.Qt.Unchecked)

    def updateSelectedLayers(self, index):
        #QMessageBox.information(self.iface.mainWindow(), "debug", "IN updateSelectedLayers: {}".format(self.model.itemFromIndex(index)))
        TOMsMessageLog.logMessage("IN updateSelectedLayers: {}".format(index) ,
                                 level=Qgis.Info)
        item = self.model.itemFromIndex(index)
        if item.checkState() == QtCore.Qt.Checked:
            self.selectedLayers.append(item)
        else:
            self.selectedLayers.remove(item)

    def getSelectedLayers(self):
        return self.selectedLayers

