# to be runwithin QGIS console
# set up layer and select feature
from TOMs.core.TOMsGeometryElement import ElementGeometryFactory
restrictionLayer = QgsProject.instance().mapLayersByName("Bays")[0]
selectedRestrictions = restrictionLayer.selectedFeatures()
currRestriction = selectedRestrictions[0]
#
# Change the GeomShapeID - and see the output ...
currGeomShapeID = currRestriction.attribute("GeomShapeID")
currRestriction[currRestriction.fields().indexFromName("GeomShapeID")] = currGeomShapeID + 20
newGeom = ElementGeometryFactory.getElementGeometry(currRestriction)