# coding=utf-8
"""Dialog test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'th@mhtc.co.uk'
__date__ = '2017-12-15'
__copyright__ = 'Copyright 2017, TH'

import unittest

#from PyQt4.QtGui import QDialogButtonBox, QDialog
from qgis.PyQt.QtWidgets import (
    QMessageBox,
    QAction,
    QDialogButtonBox,
    QLabel,
    QDockWidget, QDialog
)

from qgis.PyQt.QtGui import (
    QIcon,
    QPixmap
)

from qgis.PyQt.QtCore import (
    QObject, QTimer, pyqtSignal,
    QTranslator,
    QSettings,
    QCoreApplication,
    qVersion, QVariant
)

from qgis.core import (
    QgsExpressionContextUtils,
    QgsExpression,
    QgsFeatureRequest,
    # QgsMapLayerRegistry,
    QgsMessageLog, QgsFeature, QgsGeometry,
    QgsTransaction, QgsTransactionGroup,
    QgsProject, QgsWkbTypes,
    QgsApplication, QgsRectangle, QgsPoint, QgsPointXY, QgsVectorLayer, QgsField
)


"""from qgis.testing import (
    start_app,
    unittest,
)

from utilities import (
    compareWkt,
    unitTestDataPath,
    writeShape
)
start_app()
TEST_DATA_DIR = unitTestDataPath()
"""

from TOMsExport import TOMsExport, TOMsExportUtils

from utilities import get_qgis_app
QGIS_APP = get_qgis_app()
#IFACE = QGIS_APP[2]


# From https://github.com/qgis/QGIS/blob/master/tests/src/python/test_qgsvectorfilewriter.py

from osgeo import gdal, ogr
from qgis.testing import start_app, unittest
#from utilities import writeShape, compareWkt, unitTestDataPath

#TEST_DATA_DIR = unitTestDataPath()
#start_app()

"""qgs = QgsApplication([], False)
QgsApplication.setPrefixPath("C:\QGIS_310\apps\qgis-ltr", True)
QgsApplication.initQgis()"""

class DummyInterface(object):
    def __getattr__(self, *args, **kwargs):
        def dummy(*args, **kwargs):
            return self
        return dummy
    def __iter__(self):
        return self
    def next(self):
        raise StopIteration
    def layers(self):
        # simulate iface.legendInterface().layers()
        return QgsProject.instance().mapLayersByName()

iface = DummyInterface()

class TOMsExportTest(unittest.TestCase):
    """Test dialog works."""

    def setUp(self):
        """Runs before each test."""
        #self.dialog = TOMsSnapTraceDialog(None)
        #QGIS_APP, CANVAS, iface, PARENT = get_qgis_app()
        #iface = DummyInterface()

        self.testClass = TOMsExportUtils(iface)

    def tearDown(self):
        """Runs after each test."""
        self.dialog = None

    def test_isThisTOMsLayer(self):

        #self.testData()
        testLayerA = QgsVectorLayer(
            ('LineString?crs=epsg:27700&index=yes'),
            'test1',
            'memory')
        testProviderA = testLayerA.dataProvider()

        testLineString1 = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0), QgsPointXY(1, 0)]
        )
        testLineString2 = QgsGeometry.fromPolylineXY(
            [QgsPointXY(1, 0), QgsPointXY(1, 1)]
        )
        testLineString3 = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0), QgsPointXY(-1, 1)]
        )
        testLineString4 = QgsGeometry.fromPolylineXY(
            [QgsPointXY(1, 1), QgsPointXY(2, 1)]
        )

        testProviderA.addAttributes([QgsField("GeometryID", QVariant.String),
                                    QgsField("age", QVariant.Int),
                                    QgsField("size", QVariant.Double),
                                    QgsField("size2", QVariant.Double)])
        testFieldsA = testProviderA.fields()
        """for field in testFields:
            print ('** {}'.format(field.name()))"""

        testFeature1 = QgsFeature(testFieldsA)
        testFeature1.setGeometry(testLineString1)
        testFeature1.setAttributes(["Smith", 20, 0.3])
        testProviderA.addFeatures([testFeature1])

        testFeature2 = QgsFeature(testFieldsA)
        testFeature2.setGeometry(testLineString2)
        testFeature2.setAttributes(["Blogs", 20, 0.3])
        testProviderA.addFeatures([testFeature2])

        # check field called "OpenDate" does not exist
        result = self.testClass.isThisTOMsLayer(testLayerA)
        self.assertFalse(result)

        # check field called "OpenDate" does exist but is NULL

        testLayerB = QgsVectorLayer(
            ('LineString?crs=epsg:27700&index=yes'),
            'test2',
            'memory')
        testProviderB = testLayerB.dataProvider()
        testProviderB.addAttributes([QgsField("OpenDate", QVariant.String)])
        testFieldsB = testProviderB.fields()
        testFeature3 = QgsFeature(testFieldsB)
        testFeature3.setGeometry(testLineString2)
        testProviderB.addFeatures([testFeature3])

        result = self.testClass.isThisTOMsLayer(testLayerB)
        self.assertFalse(result)

        # check field called "OpenDate" does exist but is not NULL
        testFeature3.setAttribute("OpenDate", 'Test')
        testProviderB.addFeatures([testFeature3])

        #print ('*************************** Count: {}'.format(testLayerB.featureCount()))
        testLayerB.reload()
        for field in testLayerB.fields():
            print ('+++ field: {}'.format(field.name()))

        result = self.testClass.isThisTOMsLayer(testLayerB)
        self.assertTrue(result)

    def test_setFieldsForTOMsExportLayer(self):

        TOMsRequiredFields = ["GeometryID", "RestrictionTypeID", "RestType", "NrBays", "TimePeriodID", "PayTypeID", "MaxStayID", "NoReturnID",
                                        "BaysWordingID", "RoadName", "USRN", "OpenDate",
                                        "CPZ", "ParkingTariffArea", "Restriction_Length",   # for bays
                                   "NoWaitingTimeID", "NoLoadingTimeID",    # for lines
                                   "AreaPermitCode"  # for polygons
                                   ]
        testLayerA = QgsVectorLayer(
            ('LineString?crs=epsg:27700&index=yes'),
            'test1',
            'memory')
        testProviderA = testLayerA.dataProvider()
        testProviderA.addAttributes([QgsField("GeometryID", QVariant.String),
                                    QgsField("RestrictionTypeID", QVariant.Int),
                                    QgsField("NrBays", QVariant.Int),
                                    QgsField("size2", QVariant.Double)])
        testLayerA.reload()

        reqFields = self.testClass.setFieldsForTOMsExportLayer(testLayerA, TOMsRequiredFields)
        self.assertEqual(len(reqFields), 3)

    def test_getRestrictionGeometryWkbType(self):
        testLayerA = QgsVectorLayer(
            ('LineString?crs=epsg:27700&index=yes'),
            'test1',
            'memory')
        testProviderA = testLayerA.dataProvider()

        testLineString1 = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0), QgsPointXY(1, 0)]
        )

        testProviderA.addAttributes([QgsField("GeometryID", QVariant.String),
                                     QgsField("GeomShapeID", QVariant.Int)
                                     ])
        testFieldsA = testProviderA.fields()
        """for field in testFields:
            print ('** {}'.format(field.name()))"""

        testFeature1 = QgsFeature(testFieldsA)
        testFeature1.setGeometry(testLineString1)
        testFeature1.setAttributes(["Smith", 1])
        testProviderA.addFeatures([testFeature1])


        layerGeomWkbType = QgsWkbTypes.LineString

        restrictionGeomWkbType = self.testClass.getRestrictionGeometryWkbType(testFeature1, layerGeomWkbType)
        self.assertEqual(restrictionGeomWkbType, QgsWkbTypes.MultiLineString)

        testFeature2 = QgsFeature(testFieldsA)
        testFeature2.setGeometry(testLineString1)
        testFeature2.setAttributes(["Smith", 21])
        testProviderA.addFeatures([testFeature2])

        restrictionGeomWkbType = self.testClass.getRestrictionGeometryWkbType(testFeature2, layerGeomWkbType)
        self.assertEqual(restrictionGeomWkbType, QgsWkbTypes.MultiPolygon)

    def test_prepareNewLayer(self):

        testLayerA = QgsVectorLayer(
            ('{type}?crs=epsg:27700&index=yes'.format(type=QgsWkbTypes.displayString(QgsWkbTypes.LineString))),
            'test1',
            'memory')
        self.assertEqual(testLayerA.wkbType(), QgsWkbTypes.LineString)
        #print ('++++++ testLayerA type: {}'.format(QgsWkbTypes.displayString(testLayerA.wkbType())))

        testProviderA = testLayerA.dataProvider()

        testLineString1 = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0), QgsPointXY(1, 0)]
        )

        testProviderA.addAttributes([QgsField("GeometryID", QVariant.String),
                                    QgsField("RestrictionTypeID", QVariant.Int),
                                    QgsField("GeomShapeID", QVariant.Int),
                                    QgsField("AzimuthToRoadCentreLine", QVariant.Double)])
        testFieldsA = testProviderA.fields()
        """for field in testFields:
            print ('** {}'.format(field.name()))"""

        testFeature1 = QgsFeature(testFieldsA)
        testFeature1.setGeometry(testLineString1)
        testFeature1.setAttributes(["Smith", 101, 1, 0])
        testProviderA.addFeatures([testFeature1])
        testLayerA.reload()

        #print ('++++++ type: {}'.format(QgsWkbTypes.displayString(QgsWkbTypes.LineString)))
        self.assertEqual(testLayerA.wkbType(), QgsWkbTypes.LineString)

        requiredFields = [QgsField("GeometryID", QVariant.String),
                          QgsField("RestrictionTypeID", QVariant.Int)
                                   ]
        newLayerName = 'Test1_3'
        geomWbkType = QgsWkbTypes.MultiLineString

        newLayer = self.testClass.prepareNewLayer(testLayerA, newLayerName, geomWbkType, requiredFields)
        self.assertIsNotNone(newLayer)
        self.assertEqual(newLayer.fields().count(), 2)
        #print ('++++++ new type: {}'.format(QgsWkbTypes.displayString(newLayer.wkbType())))
        self.assertEqual(newLayer.wkbType(), QgsWkbTypes.MultiLineString)
        print ('==== newLayer crs:'.format(newLayer.crs().authid()))

    def test_processRestriction(self):
        testLayerA = QgsVectorLayer(
            ('{type}?crs=epsg:27700&index=yes'.format(type=QgsWkbTypes.displayString(QgsWkbTypes.LineString))),
            'test1',
            'memory')
        self.assertEqual(testLayerA.wkbType(), QgsWkbTypes.LineString)
        #print ('++++++ testLayerA type: {}'.format(QgsWkbTypes.displayString(testLayerA.wkbType())))

        testProviderA = testLayerA.dataProvider()

        testLineString1 = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0), QgsPointXY(1, 0)]
        )

        testProviderA.addAttributes([QgsField("GeometryID", QVariant.String),
                                    QgsField("RestrictionTypeID", QVariant.Int),
                                    QgsField("GeomShapeID", QVariant.Int),
                                    QgsField("AzimuthToRoadCentreLine", QVariant.Double)])
        testFieldsA = testProviderA.fields()
        """for field in testFields:
            print ('** {}'.format(field.name()))"""

        testFeature1 = QgsFeature(testFieldsA)
        testFeature1.setGeometry(testLineString1)
        testFeature1.setAttributes(["Smith", 101, 1, 0])
        testProviderA.addFeatures([testFeature1])
        testLayerA.reload()

        self.testClass.processRestriction(testFeature1, testLayerA)
        print ('*************************** Count: {}'.format(testLayerA.featureCount()))
        self.assertEqual(testLayerA.featureCount(), 2)

    def test_saveLayerToGpkg(self):
        testLayerA = QgsVectorLayer(
            ('{type}?crs=epsg:27700&index=yes'.format(type=QgsWkbTypes.displayString(QgsWkbTypes.MultiLineString))),
            'testA',
            'memory')
        self.assertEqual(testLayerA.wkbType(), QgsWkbTypes.MultiLineString)
        #print ('++++++ testLayerA type: {}'.format(QgsWkbTypes.displayString(testLayerA.wkbType())))

        testProviderA = testLayerA.dataProvider()

        testLineString1 = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0), QgsPointXY(1, 0)]
        )

        testProviderA.addAttributes([QgsField("GeometryID", QVariant.String),
                                    QgsField("RestrictionTypeID", QVariant.Int),
                                    QgsField("GeomShapeID", QVariant.Int),
                                    QgsField("AzimuthToRoadCentreLine", QVariant.Double)])
        testFieldsA = testProviderA.fields()
        """for field in testFields:
            print ('** {}'.format(field.name()))"""

        testFeature1 = QgsFeature(testFieldsA)
        testFeature1.setGeometry(testLineString1)
        testFeature1.setAttributes(["Smith", 101, 1, 0])
        testProviderA.addFeatures([testFeature1])
        testLayerA.reload()

        fileName = 'C:\\Users\\marie_000\\Documents\\MHTC\\tmp\\test1.gpkg'
        self.testClass.saveLayerToGpkg(testLayerA, fileName)

        ds = ogr.Open(fileName)
        lyr = ds.GetLayerByName('testA')
        self.assertIsNotNone(lyr)
        f = lyr.GetNextFeature()
        self.assertEqual(f['GeometryID'], 'Smith')

    def test_processLayer(self):
        testLayerA = QgsVectorLayer(
            ('{type}?crs=epsg:27700&index=yes'.format(type=QgsWkbTypes.displayString(QgsWkbTypes.MultiLineString))),
            'testA',
            'memory')
        self.assertEqual(testLayerA.wkbType(), QgsWkbTypes.MultiLineString)
        # print ('++++++ testLayerA type: {}'.format(QgsWkbTypes.displayString(testLayerA.wkbType())))

        testProviderA = testLayerA.dataProvider()

        testLineString1 = QgsGeometry.fromPolylineXY(
            [QgsPointXY(0, 0), QgsPointXY(1, 0)]
        )

        testProviderA.addAttributes([QgsField("GeometryID", QVariant.String),
                                     QgsField("RestrictionTypeID", QVariant.Int),
                                     QgsField("GeomShapeID", QVariant.Int),
                                     QgsField("AzimuthToRoadCentreLine", QVariant.Double)])
        testFieldsA = testProviderA.fields()
        """for field in testFields:
            print ('** {}'.format(field.name()))"""

        testFeature1 = QgsFeature(testFieldsA)
        testFeature1.setGeometry(testLineString1)
        testFeature1.setAttributes(["Smith", 101, 1, 0])
        testProviderA.addFeatures([testFeature1])
        testLayerA.reload()

        requiredFields = ["GeometryID", "RestrictionTypeID"]
        outputLayersList = self.testClass.processLayer(testLayerA, requiredFields)
        self.assertEqual(len(outputLayersList), 1)
        self.assertEqual(len(outputLayersList[0][1].fields()), 2)

if __name__ == "__main__":
    suite = unittest.makeSuite(TOMsExportTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

