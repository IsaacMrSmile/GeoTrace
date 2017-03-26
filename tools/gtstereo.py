# -*- coding: utf-8 -*-
"""
/***************************************************************************
 File Name: tools/gtstereo.py
 Last Change: 
/*************************************************************************** 
 ---------------
 GeoTools
 ---------------
 A QGIS plugin
 Collection of tools for geoscience application. Some tools can be found in 
 qCompass plugin for CloudCompare. 
 If you are publishing any work associated with this plugin please cite
 #TODO add citatioN!
                             -------------------
        begin                : 2015-01-1
        copyright          : (C) 2015 by Lachlan Grose
        email                : lachlan.grose@monash.edu
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

import os.path,  sys
import numpy as np
currentPath = os.path.dirname( __file__ )
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../'))

from PyQt4 import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import mplstereonet
import random

class Window(QtGui.QDialog):
    def __init__(self, canvas, iface, parent=None):
        super(Window, self).__init__(parent)
        self.canvas = canvas
        self.iface = iface
        self.figure, self.ax = mplstereonet.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.polesbutton = QtGui.QPushButton('Plot Poles')
        self.polesbutton.clicked.connect(self.plotpoles)
        self.circlebutton = QtGui.QPushButton('Fit Fold')
        self.circlebutton.clicked.connect(self.fitfold)
        self.densitybutton = QtGui.QPushButton('Plot Density')
        self.densitybutton.clicked.connect(self.plotdensity)
        self.resetbutton = QtGui.QPushButton('Clear Plot')
        self.resetbutton.clicked.connect(self.reset)

        self.vector_layer_combo_box = QgsMapLayerComboBox()
        self.vector_layer_combo_box.setCurrentIndex(-1)
        self.vector_layer_combo_box.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.dip_dir = QCheckBox()
        self.selected_features = QCheckBox()
        self.strike_combo_box = QgsFieldComboBox()
        self.dip_combo_box = QgsFieldComboBox()
        top_form_layout = QtGui.QFormLayout()
        layout = QtGui.QVBoxLayout()
        top_form_layout.addRow("Layer:",self.vector_layer_combo_box)
        top_form_layout.addRow("Direction:",self.strike_combo_box)
        top_form_layout.addRow("Dip:",self.dip_combo_box)
        top_form_layout.addRow("Dip Direction:",self.dip_dir)
        top_form_layout.addRow("Selected Features Only:",self.selected_features)
        self.vector_layer_combo_box.layerChanged.connect(self.strike_combo_box.setLayer)  # setLayer is a native slot function
        self.vector_layer_combo_box.layerChanged.connect(self.dip_combo_box.setLayer)  # setLayer is a native slot function
        layout.addLayout(top_form_layout)
        layout.addWidget(self.canvas)
        #layout.addWidget(self.strike_combo)
        #layout.addWidget(self.dip_combo)
        bottom_form_layout = QtGui.QFormLayout()
        bottom_form_layout.addWidget(self.polesbutton)
        bottom_form_layout.addWidget(self.circlebutton)
        bottom_form_layout.addWidget(self.densitybutton)
        bottom_form_layout.addWidget(self.resetbutton)
        layout.addLayout(bottom_form_layout)
        self.setLayout(layout)
    def onclick(self,event):
        strike, dip = mplstereonet.stereonet_math.geographic2pole(event.xdata,event.ydata)
        self.ax.plane(strike,dip)
        self.canvas.draw()
    def plotpoles(self):
        strike, dip = self.get_strike_dip()
        self.ax.hold(False)
        self.ax.hold(True)
        self.ax.pole(strike, dip)
        self.ax.grid(True)
        self.canvas.draw()
    def reset(self):
        #hack to reset graph, just plot nothing
        strike = []
        dip = []
        self.ax.hold(False)
        self.ax.plane(strike, dip)
        self.ax.grid(True)
        self.canvas.draw()

    def get_strike_dip(self):
        strike = []
        dip = []
        dip_name = self.dip_combo_box.currentField()
        strike_name = self.strike_combo_box.currentField()

        features = self.vector_layer_combo_box.currentLayer().getFeatures()
        if self.selected_features.isChecked() == True:
            features = self.vector_layer_combo_box.currentLayer().selectedFeaturesIterator()
        for f in features:
            dip.append(f[dip_name]) #self.dip_combo.currentText()])
            if self.dip_dir.isChecked() == True:
                strike.append(f[strike_name]+90)
            else:
                strike.append(f[strike_name])#self.strike_combo.currentText()]) 
        return strike, dip
    def plotdensity(self):
        strike, dip = self.get_strike_dip()
        # discards the old graph
        self.ax.hold(False)
        self.ax.hold(True)

        self.ax.density_contourf(strike,dip,measurement='poles')
        self.ax.pole(strike, dip)
        self.ax.grid(True)
        # refresh canvas
        self.canvas.draw()

    def plotcircles(self):
        strike, dip = self.get_strike_dip()
        self.ax.hold(False)
        self.ax.plane(strike, dip)
        self.ax.grid()

        # refresh canvas
        self.canvas.draw()
    def fitfold(self):
        strike, dip = self.get_strike_dip()
                # discards the old graph
        self.ax.hold(True)
        fit_strike,fit_dip = mplstereonet.fit_girdle(strike,dip)
        lon, lat = mplstereonet.pole(fit_strike, fit_dip)
        (plunge,), (bearing,) = mplstereonet.pole2plunge_bearing(fit_strike, fit_dip)       
        template = u'Plunge / Direction of Fold Axis\n{:02.0f}\u00b0/{:03.0f}\u00b0'
        self.ax.annotate(template.format(plunge, bearing), ha='center', va='bottom',
            xy=(lon, lat), xytext=(-50, 20), textcoords='offset points',
            arrowprops=dict(arrowstyle='-|>', facecolor='black'))

        self.ax.plane(fit_strike, fit_dip, color='red', lw=2)
        self.ax.pole(fit_strike, fit_dip, marker='o', color='red', markersize=14)
        self.canvas.draw() 
class GtStereo():
  def __init__(self, canvas,iface):
      self.canvas = canvas
      self.iface = iface

        
  def run(self):
        """Run method that performs all the real work"""

        self.main = Window(self.canvas,self.iface)
        # show the dialog
        self.main.show()
        # Run the dialog event loop
        #result = self.dlg.exec_()
        # See if OK was pressed
        #if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
         #   pass      
