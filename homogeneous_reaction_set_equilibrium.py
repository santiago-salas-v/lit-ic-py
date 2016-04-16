# -*- coding: utf-8 -*-
"""
Created on Fri Nov 27 20:48:42 2015

@author: Santiago Salas
@ref: Denbigh, p. 298
"""
import os
import sys
import logging
import re
import pandas as pd
import numpy as np
import csv
import bisect
import uuid
import matplotlib
import colormaps
from functools import partial
from mat_Zerlegungen import gausselimination
from datetime import datetime

matplotlib.use('Qt4Agg')
matplotlib.rcParams['backend.qt4'] = 'PySide'
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PySide import QtGui, QtCore
from mpldatacursor import datacursor

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromutf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8

    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


def take_float(x):
    return float(x.rpartition('=')[-1])


def take_list(x):
    return np.fromstring(x.rpartition('=')[-1]
                         .replace('[', '').replace(']', ''),
                         sep=',')


def take_int(x):
    return int(x.rpartition('=')[-1])


def take_bool(x):
    return x.rpartition('=')[-1] == 'True'


def take_date(x):
    return datetime.strptime(x, '%Y-%m-%d %H:%M:%S,%f')


colormap_colors = colormaps.viridis.colors + colormaps.inferno.colors
markers = matplotlib.markers.MarkerStyle.filled_markers
fillstyles = matplotlib.markers.MarkerStyle.fillstyles
float_re = re.compile(r'(([+-]?\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)')
matchingHLine = re.compile('=+')
reac_headers_re = re.compile(
    r'nu_?i?([0-9]+)?j(\(i=([0-9]+)\))?' +
    r'|(^pKaj$)')  # For now, no more than 999 reactions
comp_headers_re = re.compile(
    r'(Comp\.?i?)|(z_?i?|Z_?i?)|(C_?0_?i?)')


class UiGroupBox(QtGui.QWidget):
    _was_canceled = False

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        # Default size
        parent.resize(500, 357)
        # Assignments
        self.verticalLayout_2 = QtGui.QVBoxLayout(parent)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.open_button = QtGui.QPushButton()
        self.save_button = QtGui.QPushButton()
        self.info_button = QtGui.QPushButton()
        self.log_button = QtGui.QPushButton()
        self.horizontalLayout_5 = QtGui.QHBoxLayout()
        self.label_3 = QtGui.QLabel()
        self.equilibrate_button = QtGui.QPushButton()
        self.spinBox_3 = QtGui.QSpinBox()
        self.label_4 = QtGui.QLabel()
        self.label = QtGui.QLabel()
        self.spinBox = QtGui.QSpinBox()
        self.tableComps = QtGui.QTableWidget()
        self.label_9 = QtGui.QLabel()
        self.progress_var = QtGui.QProgressBar(parent)
        self.cancelButton = QtGui.QPushButton(parent)
        self.doubleSpinBox_5 = ScientificDoubleSpinBox()
        item = QtGui.QTableWidgetItem()
        self.horizontalLayout_7 = QtGui.QHBoxLayout()
        self.horizontalLayout_6 = QtGui.QHBoxLayout()
        self.label_5 = QtGui.QLabel()
        self.comboBox_3 = QtGui.QComboBox()
        self.label_6 = QtGui.QLabel()
        self.doubleSpinBox_6 = QtGui.QDoubleSpinBox()
        self.label_2 = QtGui.QLabel()
        self.spinBox_2 = QtGui.QSpinBox()
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.tableReacs = QtGui.QTableWidget()
        self.verticalLayout = QtGui.QVBoxLayout()
        self.label_7 = QtGui.QLabel()
        self.comboBox = QtGui.QComboBox()
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.doubleSpinBox = ScientificDoubleSpinBox()
        self.doubleSpinBox_2 = ScientificDoubleSpinBox()
        self.plotButton = QtGui.QPushButton()
        self.radio_group = QtGui.QHBoxLayout()
        self.radio_b_1 = QtGui.QRadioButton()
        self.radio_b_2 = QtGui.QRadioButton()
        self.radio_b_3 = QtGui.QRadioButton()
        self.groupBox = None  # self.groupBox will contain either the plotBox or logBox
        # Object names
        parent.setObjectName(_fromutf8("GroupBox"))
        self.verticalLayout_2.setObjectName(_fromutf8("verticalLayout_2"))
        self.horizontalLayout_2.setObjectName(_fromutf8("horizontalLayout_2"))
        self.horizontalLayout_3.setObjectName(_fromutf8("horizontalLayout_3"))
        self.open_button.setObjectName(_fromutf8("open_button"))
        self.save_button.setObjectName(_fromutf8("save_button"))
        self.info_button.setObjectName(_fromutf8("info_button"))
        self.log_button.setObjectName(_fromutf8("log_button"))
        self.horizontalLayout_5.setObjectName(_fromutf8("horizontalLayout_5"))
        self.label_3.setObjectName(_fromutf8("max_it_label"))
        self.spinBox_3.setObjectName(_fromutf8("max_it_spinbox"))
        self.label_4.setObjectName(_fromutf8("tol_label"))
        self.doubleSpinBox_5.setObjectName(_fromutf8("tol_spinbox"))
        self.label.setObjectName(_fromutf8("label"))
        self.spinBox.setObjectName(_fromutf8("spinBox"))
        self.tableComps.setObjectName(_fromutf8("tableComps"))
        self.horizontalLayout_6.setObjectName(_fromutf8("horizontalLayout_6"))
        self.label_5.setObjectName(_fromutf8("solvent_label"))
        self.label_6.setObjectName(_fromutf8("c_solvent_tref"))
        self.doubleSpinBox_6.setObjectName(
            _fromutf8("c_solvent_tref_doublespinbox"))
        self.label_2.setObjectName(_fromutf8("label_2"))
        self.spinBox_2.setObjectName(_fromutf8("spinBox_2"))
        self.horizontalLayout.setObjectName(_fromutf8("horizontalLayout"))
        self.tableReacs.setObjectName(_fromutf8("tableReacs"))
        self.verticalLayout.setObjectName(_fromutf8("verticalLayout"))
        self.label_7.setObjectName(_fromutf8("horizontalAxisLabel"))
        self.comboBox.setObjectName(_fromutf8("comboBox"))
        self.horizontalLayout_3.setObjectName(_fromutf8("horizontalLayout_3"))
        self.doubleSpinBox.setObjectName(_fromutf8("doubleSpinBox"))
        self.doubleSpinBox_2.setObjectName(_fromutf8("doubleSpinBox_2"))
        self.plotButton.setObjectName(_fromutf8("plotButton"))
        self.radio_group.setObjectName(_fromutf8("radio_group"))
        self.radio_b_1.setObjectName(_fromutf8("radio_b_1"))
        self.radio_b_2.setObjectName(_fromutf8("radio_b_2"))
        self.radio_b_3.setObjectName(_fromutf8("radio_b_3"))
        # Operations
        self.horizontalLayout_2.addWidget(self.open_button)
        self.horizontalLayout_2.addWidget(self.save_button)
        self.horizontalLayout_2.addWidget(self.log_button)
        self.horizontalLayout_2.addWidget(self.info_button)
        self.verticalLayout_2.addWidget(self.equilibrate_button)
        self.radio_group.addWidget(self.radio_b_1)
        self.radio_group.addWidget(self.radio_b_2)
        self.radio_group.addWidget(self.radio_b_3)
        self.radio_b_1.setChecked(True)
        self.radio_b_2.setEnabled(False)
        self.radio_b_3.setEnabled(False)
        self.radio_b_1.setToolTip('<b>%s</b><br><img src="%s">' %
                                  ('Ideal solution',
                                   'utils/Ideal_solution.png'))
        self.radio_b_2.setToolTip('<b>%s</b><br><img src="%s">' %
                                  ('Debye-Hueckel',
                                   'utils/Debye-Hueckel.png'))
        self.radio_b_3.setToolTip('<b>%s</b><br><img src="%s">' %
                                  ('Davies (DH ext.)',
                                   'utils/Davies.png'))
        self.verticalLayout_2.addLayout(self.radio_group)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.label_3.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignCenter)
        self.horizontalLayout_5.addWidget(self.label_3)
        self.spinBox_3.setMaximum(2000)
        self.spinBox_3.setMinimum(2)
        self.spinBox_3.setProperty("value", 1000)
        self.horizontalLayout_5.addWidget(self.spinBox_3)
        self.label_4.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignCenter)
        self.horizontalLayout_5.addWidget(self.label_4)
        self.doubleSpinBox_5.setDecimals(
            int(-np.log10(np.finfo(float).eps) + 1))
        self.doubleSpinBox_5.setMaximum(float(1))
        self.doubleSpinBox_5.setMinimum(np.finfo(float).eps * 2)
        self.doubleSpinBox_5.setSingleStep(
            0.1 / 100.0 * (1.0 - np.finfo(float).eps))
        self.doubleSpinBox_5.setProperty("value", float(1.0e-08))
        self.horizontalLayout_5.addWidget(self.doubleSpinBox_5)
        self.label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignCenter)
        self.horizontalLayout_5.addWidget(self.label)
        self.spinBox.setProperty("value", 0)
        self.horizontalLayout_5.addWidget(self.spinBox)
        self.verticalLayout_2.addLayout(self.horizontalLayout_5)
        self.tableComps.setMinimumSize(QtCore.QSize(0, 210))
        item.setTextAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.tableComps.horizontalHeader().setCascadingSectionResizes(False)
        self.tableComps.horizontalHeader().setDefaultSectionSize(100)
        self.tableComps.horizontalHeader().setMinimumSectionSize(27)
        self.tableComps.horizontalHeader().setSortIndicatorShown(True)
        self.tableComps.verticalHeader().setVisible(False)
        self.verticalLayout_2.addWidget(self.tableComps)
        self.label_9.setAlignment(QtCore.Qt.AlignTop)
        self.label_9.setFrameStyle(QtGui.QFrame.Box | QtGui.QFrame.Raised)
        self.verticalLayout_2.addWidget(self.label_9)
        self.horizontalLayout_7.setAlignment(QtCore.Qt.AlignRight)
        self.horizontalLayout_7.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        self.horizontalLayout_7.addStrut(max(
            [self.progress_var.frameSize().height(),
             self.cancelButton.frameSize().height()]))
        self.horizontalLayout_7.setAlignment(QtCore.Qt.AlignLeft)
        self.horizontalLayout_7.addWidget(self.cancelButton)
        self.horizontalLayout_7.addWidget(self.progress_var)
        self.cancelButton.setEnabled(False)
        self.progress_var.setEnabled(False)
        self.verticalLayout_2.addLayout(self.horizontalLayout_7)
        self.label_5.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignCenter)
        self.horizontalLayout_6.addWidget(self.label_5)
        self.horizontalLayout_6.addWidget(self.comboBox_3)
        self.label_6.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignCenter)
        self.horizontalLayout_6.addWidget(self.label_6)
        self.doubleSpinBox_6.setDecimals(
            int(-np.log10(np.finfo(float).eps) + 1))
        self.doubleSpinBox_6.setMaximum(float(1000))
        self.doubleSpinBox_6.setMinimum(np.finfo(float).eps * 1.1)
        self.doubleSpinBox_6.setSingleStep(1.0e-2)
        self.horizontalLayout_6.addWidget(self.doubleSpinBox_6)
        self.label_2.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignCenter)
        self.horizontalLayout_6.addWidget(self.label_2)
        self.spinBox_2.setProperty("value", 0)
        self.horizontalLayout_6.addWidget(self.spinBox_2)
        self.verticalLayout_2.addLayout(self.horizontalLayout_6)
        self.tableReacs.horizontalHeader().setVisible(True)
        self.tableReacs.verticalHeader().setVisible(False)
        self.horizontalLayout.addWidget(self.tableReacs)
        self.label_7.setAlignment(
            QtCore.Qt.AlignHCenter | QtCore.Qt.AlignCenter)
        self.verticalLayout.addWidget(self.label_7)
        self.verticalLayout.addWidget(self.comboBox)
        self.doubleSpinBox.setMinimum(0.0)
        self.horizontalLayout_3.addWidget(self.doubleSpinBox)
        self.doubleSpinBox_2.setMinimum(0.0)
        self.horizontalLayout_3.addWidget(self.doubleSpinBox_2)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.verticalLayout.addWidget(self.plotButton)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        # Events
        self.open_button.clicked.connect(partial(self.open_file))
        self.save_button.clicked.connect(partial(self.save_file))
        self.plotButton.clicked.connect(partial(self.solve_intervals))
        self.equilibrate_button.clicked.connect(
            partial(self.recalculate_after_cell_edit, 0, 0))
        self.tableComps.cellChanged.connect(
            partial(self.recalculate_after_cell_edit))
        self.info_button.clicked.connect(partial(self.display_about_info))
        self.log_button.clicked.connect(partial(self.show_log))
        self.cancelButton.clicked.connect(partial(self.cancel_loop))
        self.comboBox.currentIndexChanged.connect(
            partial(self.populate_input_spinboxes))

        # Icons
        icon0 = QtGui.QIcon()
        icon0.addPixmap(QtGui.QPixmap(
            _fromutf8("utils/glyphicons-145-folder-open.png")),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(
            _fromutf8("utils/glyphicons-415-disk-save.png")),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(
            _fromutf8("utils/glyphicons-41-stats.png")),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(
            _fromutf8("utils/glyphicons-82-refresh.png")),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(
            _fromutf8("utils/glyphicons-196-circle-info.png")),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(
            _fromutf8("utils/glyphicons-88-log-book.png")),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.open_button.setIcon(icon0)
        self.save_button.setIcon(icon1)
        self.plotButton.setIcon(icon2)
        self.equilibrate_button.setIcon(icon3)
        self.info_button.setIcon(icon4)
        self.log_button.setIcon(icon5)
        # Retranslate, connect
        self.retranslate_ui(parent)
        QtCore.QMetaObject.connectSlotsByName(parent)

    def retranslate_ui(self, parent):
        parent.setWindowTitle(_translate("parent", "Homogeneous EC.", None))
        parent.setTitle(QtGui.QApplication.translate("parent", "EC", None))
        __sortingEnabled = self.tableComps.isSortingEnabled()
        self.open_button.setText(_translate("parent", "Open", None))
        self.save_button.setText(_translate("parent", "Save", None))
        self.log_button.setText(_translate("parent", "Log", None))
        self.info_button.setText(_translate("parent", "About", None))
        self.equilibrate_button.setText(
            _translate("parent", "Equilibrate", None))
        self.radio_b_1.setText(
            _translate("parent", "Ideal solution", None))
        self.radio_b_2.setText(
            _translate("parent", "Debye-Hückel", None))
        self.radio_b_3.setText(
            _translate("parent", "Davies (DH ext.)", None))
        self.tableComps.setSortingEnabled(__sortingEnabled)
        self.plotButton.setText(_translate("parent", "Plot", None))
        self.label_2.setText(_translate("parent", "nr (Reac.)", None))
        self.label.setText(_translate("parent", "n (Comp.)", None))
        self.label_3.setText(_translate("parent", "max. it", None))
        self.label_4.setText(_translate("parent", "tol", None))
        self.label_5.setText(_translate("parent", "solvent", None))
        self.label_6.setText(_translate("parent", "C_solvent (25C)", None))
        self.label_7.setText(_translate("parent", "Horizontal 'X' axis", None))
        self.label_9.setText(
            _translate(
                "parent",
                'Currently unequilibrated',
                None))
        self.cancelButton.setText('cancel')

    def cancel_loop(self):
        self._was_canceled = True
        self.progress_var.setValue(0)

    def populate_input_spinboxes(self, index):
        comps = self.comps
        c0_component = self.c0_i[index]
        self.doubleSpinBox.setValue(c0_component / 10.0 ** 7)
        self.doubleSpinBox_2.setValue(c0_component * (1 + 20 / 100.0))

    def remove_canceled_status(self):
        self._was_canceled = False

    def was_canceled(self):
        return self._was_canceled

    def open_file(self):
        (filename, _) = \
            QtGui.QFileDialog.getOpenFileName(None,
                                              caption='Open file',
                                              dir=os.path.join(sys.path[0], 'DATA'),
                                              filter='*.csv')
        if os.path.isfile(filename):
            # Reset solution state and order of items
            del self.acceptable_solution
            if hasattr(self, 'component_order_in_table'):
                delattr(self, 'component_order_in_table')
            # Load csv data into form variables
            self.load_csv(filename)

            # Continue with typical solution and table population procedure
            self.gui_equilibrate()
            self.tableComps.sortByColumn(0, QtCore.Qt.AscendingOrder)
            self.tableReacs.sortByColumn(0, QtCore.Qt.AscendingOrder)

    def load_csv(self, filename):
        with open(filename) as csv_file:
            n = 0
            nr = 0
            header_comps = []
            header_reacs = []
            reader = csv.reader(csv_file, dialect='excel')
            reading_comps = False
            reading_reacs = False
            comps = []
            reacs = []
            valid_columns_reacs = []
            valid_columns_comps = []
            for row in reader:
                row_without_whitespace = [x.replace(' ', '') for x in row]
                row_without_blanks = [
                    x for x in row_without_whitespace if len(x) > 0]
                if len(row_without_blanks) == 0:
                    pass  # skip empty line
                elif 'COMP' in row:
                    reading_comps = True
                    reading_reacs = False
                    header_comps = next(reader)
                    valid_columns_comps = [header_comps.index(x)
                                           for x in header_comps if
                                           x.replace(' ', '') != '']
                    header_comps = [header_comps[x].replace(' ', '')
                                    for x in valid_columns_comps]
                elif 'REAC' in row:
                    reading_reacs = True
                    reading_comps = False
                    header_reacs = next(reader)
                    valid_columns_reacs = [header_reacs.index(x)
                                           for x in header_reacs if
                                           x.replace(' ', '') != '']
                    header_reacs = [header_reacs[x].replace(' ', '')
                                    for x in valid_columns_reacs]
                elif reading_comps:
                    n += 1
                    # put 0 instead of blank and keep only columns to add
                    row_to_add = ['0' if row_without_whitespace[x] == '' else
                                  row_without_whitespace[x] for x in valid_columns_comps]
                    comps.append(row_to_add)
                elif reading_reacs:
                    nr += 1
                    # put 0 instead of blank and keep only columns to add
                    row_to_add = ['0' if row_without_whitespace[x] == '' else
                                  row_without_whitespace[x] for x in valid_columns_reacs]
                    reacs.append(row_to_add)
        csv_file.close()
        # Rearrange reacs to pKaj nu_ij (i=1) nu_ij(i=2) ... nu_ij(i=n)
        # Rearrange comps rearrange to Comp. i zi c0_i
        header_reacs_groups = [
            x.groups() if x is not None else x for x in map(
                lambda y: reac_headers_re.match(y), header_reacs)]
        header_comps_groups = [
            x.groups() if x is not None else x for x in map(
                lambda y: comp_headers_re.match(y), header_comps)]
        priorities_reacs = []
        priorities_comps = []
        for row in header_reacs_groups:
            if row is None:  # j or other. Irrelevant, it will be re-indexed
                priorities_reacs.append((-1, row))
            elif row[3] is not None:  # pKaj
                priorities_reacs.append((0, row[3]))
            elif row[0] is not None:  # if spec. as nu_xj(i=y), prioritize x
                priorities_reacs.append((int(row[0]), 'i=' + row[0]))
            elif row[0] is None \
                    and row[2] is not None:
                priorities_reacs.append((int(row[2]), 'i=' + row[2]))
        for row in header_comps_groups:
            if row is None:
                priorities_comps.append((-1, row))
            elif row[0] is not None:  # Comp. i
                priorities_comps.append((0, row[0]))
            elif row[1] is not None:  # zi
                priorities_comps.append((1, row[1]))
            elif row[2] is not None:  # c0_i
                priorities_comps.append((2, row[2]))
        # reacs header, form [None, ..., None, 'pKaj', i=1', 'i=2', ... 'i=n']
        # comps header, form [None, ..., None, 'Comp. i', 'z_i', 'c0_i']
        sorted_priorities_reacs = sorted(priorities_reacs, key=lambda y: y[0])
        sorted_priorities_comps = sorted(priorities_comps, key=lambda y: y[0])
        sort_indexes_reacs = [priorities_reacs.index(
            x) for x in sorted_priorities_reacs if x[1] is not None]
        sort_indexes_comps = [priorities_comps.index(
            x) for x in sorted_priorities_comps if x[1] is not None]
        sorted_reacs = []
        k = 1
        for row in reacs:
            # Add reaction index form ['j', 'pKaj', i=1, i=2, ... i=n]
            sorted_reacs.append([str(k)] + [row[x]
                                            for x in sort_indexes_reacs])
            k += 1
        header_reacs = \
            ['j'] + \
            [str(x[1]) for x in sorted_priorities_reacs if x[1] is not None]
        sorted_comps = []
        k = 1
        for row in comps:
            # Add components index form ['i', 'Comp. i', 'z_i']
            sorted_comps.append([str(k)] + [row[x]
                                            for x in sort_indexes_comps])
            k += 1
        header_comps = \
            ['i'] + \
            [str(x[1]) for x in sorted_priorities_comps if x[1] is not None]
        comps = np.array(sorted_comps)
        reacs = np.array(sorted_reacs)
        self.spinBox.setProperty("value", n)
        self.spinBox_2.setProperty("value", nr)
        self.tableComps.setRowCount(n)
        self.tableComps.setColumnCount(len(header_comps) + 3)
        self.tableComps.setHorizontalHeaderLabels(
            header_comps + ['ceq_i, mol/L', '-log10(c0_i)', '-log10(ceq_i)'])

        self.tableReacs.setRowCount(nr)
        self.tableReacs.setColumnCount(n + 2 + 1)
        self.tableReacs.setHorizontalHeaderLabels(
            header_reacs + ['xieq_i'])

        # Pass variables to self before loop start
        variables_to_pass = ['header_comps', 'comps', 'header_reacs', 'reacs',
                             'n', 'nr']
        for var in variables_to_pass:
            setattr(self, var, locals()[var])

    def load_variables_from_form(self):
        n = self.n
        nr = self.nr
        comps = np.empty([n, 4], dtype='S50')
        reacs = np.empty([nr, n + 2], dtype='S50')
        header_comps = []
        header_reacs = []
        component_order_in_table = []
        for i in range(self.tableComps.rowCount()):
            component_order_in_table.append(
                int(self.tableComps.item(i, 0).text()) - 1)
        for i in range(comps.shape[1]):
            header_comps.append(
                self.tableComps.horizontalHeaderItem(i).data(0))
        for i in range(reacs.shape[1]):
            header_reacs.append(
                self.tableReacs.horizontalHeaderItem(i).data(0))
        for j in range(comps.shape[1]):
            for i in range(comps.shape[0]):
                comps[
                    component_order_in_table[i],
                    j] = self.tableComps.item(
                    i,
                    j).text()
        for j in range(reacs.shape[1]):
            for i in range(reacs.shape[0]):
                reacs[i, j] = self.tableReacs.item(i, j).text()
        # Pass variables to self before loop start
        variables_to_pass = ['header_comps', 'comps', 'header_reacs', 'reacs',
                             'component_order_in_table']
        for var in variables_to_pass:
            setattr(self, var, locals()[var])

    def gui_setup_and_variables(self):
        # Collect variables
        n = self.n
        nr = self.nr
        comps = self.comps
        reacs = self.reacs
        # Gui setup with calculated values

        c0_i = np.matrix([row[3] for row in comps], dtype=float).T
        highest_c0_indexes = np.argpartition(c0_i.A1, (-1, -2))
        index_of_solvent = highest_c0_indexes[-1]
        c_solvent_tref = c0_i[index_of_solvent].item()
        if len(c0_i) > 1:
            index_of_second_highest_c0 = highest_c0_indexes[-2]
        else:
            index_of_second_highest_c0 = highest_c0_indexes[-1]
        c_second_highest_c0_tref = c0_i[index_of_second_highest_c0].item()

        self.c0_i = c0_i
        self.index_of_solvent = index_of_solvent
        self.c_solvent_tref = c_solvent_tref
        self.z_i = np.matrix([row[2] for row in comps], dtype=float).T
        self.nu_ij = np.matrix([row[2:2 + n] for row in reacs], dtype=int).T
        self.pka_j = np.matrix([row[1] for row in reacs], dtype=float).T
        self.max_it = int(self.spinBox_3.value())
        self.tol = float(self.doubleSpinBox_5.value())
        self.C_second_highest_C0_Tref = c_second_highest_c0_tref

        self.comboBox.clear()
        self.comboBox_3.clear()
        for item in comps[:, 0:2]:
            self.comboBox.addItem('C0_' + item[0] + ' {' + item[1] + '}')
            self.comboBox_3.addItem(item[1])
        self.comboBox.setCurrentIndex(index_of_second_highest_c0)
        self.doubleSpinBox.setValue(c_second_highest_c0_tref / 10.0 ** 7)
        self.doubleSpinBox_2.setValue(
            c_second_highest_c0_tref * (1 + 20 / 100.0))
        self.comboBox_3.setCurrentIndex(index_of_solvent)
        self.doubleSpinBox_6.setValue(c_solvent_tref)
        self.doubleSpinBox_6.setPrefix('(mol/L)')

    def retabulate(self):
        # Collect variables
        n = self.n
        nr = self.nr
        c0_i = self.c0_i
        comps = self.comps
        reacs = self.reacs
        header_comps = self.header_comps
        header_reacs = self.header_reacs
        ceq_i = self.ceq_i
        xieq_i = self.xieq_i
        if hasattr(self, 'component_order_in_table'):
            i = getattr(self, 'component_order_in_table')
        else:
            i = range(0, n)
        j = range(0, 4 + 3)

        self.tableComps.blockSignals(True)
        self.tableReacs.blockSignals(True)
        self.comboBox.blockSignals(True)
        # As usual, problems occurr when sorting is combined with setting QTableWidgetItems.
        # Therefore disable sorting, then set QTableWidgetItems and finally
        # reenable sorting.
        self.tableComps.setSortingEnabled(False)
        self.tableReacs.setSortingEnabled(False)

        for column in j:
            for row in i:
                if column < 4:
                    new_item = QtGui.QTableWidgetItem(str(comps[row, column]))
                elif column == 4:
                    new_item = QtGui.QTableWidgetItem(str(ceq_i[row].item()))
                elif column == 5:
                    if c0_i[row] <= 0:
                        new_item = QtGui.QTableWidgetItem(str(np.nan))
                    else:
                        new_item = QtGui.QTableWidgetItem(
                            str(-np.log10(c0_i[row].item())))
                elif column == 6:
                    if ceq_i[row].item() <= 0:
                        new_item = QtGui.QTableWidgetItem(str(np.nan))
                    else:
                        new_item = QtGui.QTableWidgetItem(
                            str(-np.log10(ceq_i[row].item())))
                # sortierbar machen
                if column != 1:  # Comp. i <Str>
                    new_item = NSortableTableWidgetItem(new_item)
                    self.tableComps.setItem(row, column, new_item)
                else:
                    self.tableComps.setItem(row, column, new_item)
                if column not in range(1, 3 + 1):
                    new_item.setFlags(QtCore.Qt.ItemIsEnabled)

        i = range(0, nr)
        j = range(0, n + 2 + 1)

        for column in j:
            for row in i:
                if column != n + 2:
                    self.tableReacs.setItem(
                        row, column, NSortableTableWidgetItem(str(reacs[row][column])))
                elif column == n + 2:
                    self.tableReacs.setItem(
                        row, column, NSortableTableWidgetItem(str(xieq_i[row].item())))

        # Widths and heights, re-enable sorting
        self.tableComps.setSortingEnabled(True)
        self.tableComps.horizontalHeader().setResizeMode(
            QtGui.QHeaderView.ResizeToContents)
        self.tableComps.verticalHeader().setResizeMode(
            QtGui.QHeaderView.ResizeToContents)

        self.tableReacs.setSortingEnabled(True)
        self.tableReacs.horizontalHeader().setResizeMode(
            QtGui.QHeaderView.ResizeToContents)
        self.tableReacs.verticalHeader().setResizeMode(
            QtGui.QHeaderView.ResizeToContents)

        self.tableComps.blockSignals(False)
        self.tableReacs.blockSignals(False)
        self.comboBox.blockSignals(False)

    def save_file(self):
        pass

    def solve_intervals(self):
        variables_to_check = [
            'ceq_series',
            'xieq_series',
            'indep_var_series',
            'dep_var_series',
            'index_of_variable']
        for var in variables_to_check:
            if hasattr(self, var):
                delattr(self, var)
        comps = self.comps
        reacs = self.reacs
        c0_i = self.c0_i
        n = self.n
        nr = self.nr
        index_of_variable = self.comboBox.currentIndex()
        indep_var_label = 'C0_{' + comps[index_of_variable, 0] + ', ' + \
                          comps[index_of_variable, 1] + '}/(mol/L)'
        dep_var_labels = \
            ['Ceq_' + '{' + item[0] + ', ' + item[1] + '}/(mol/L)' for item in comps[:, 0:2]] + \
            ['\\xi eq_' + '{' + str(item) + '}/(mol/L)' for item in range(1, nr + 1, 1)]
        min_value = self.doubleSpinBox.value()
        max_value = self.doubleSpinBox_2.value()
        n_points = 20
        indep_var_series_single = \
            [min_value + x
             for x in np.arange(n_points + 1) * (max_value - min_value) / n_points]
        c0_variable_comp = c0_i[index_of_variable]
        mid_index = bisect.bisect(
            indep_var_series_single,
            c0_variable_comp) - 1
        xieq_i = self.xieq_i
        ceq_i = self.ceq_i
        ceq_series = np.matrix(np.zeros([n_points + 1, len(ceq_i)]))
        xieq_series = np.matrix(np.zeros([n_points + 1, len(xieq_i)]))
        dep_var_series = dict(
            zip(dep_var_labels, np.empty(n + nr, dtype=np.ndarray)))
        indep_var_series = dict.fromkeys(
            dep_var_labels, indep_var_series_single)
        # Keep current solution intact for after plotting range
        self.stored_solution_ceq_i = self.ceq_i
        self.stored_solution_xieq_i = self.xieq_i
        for j in range(mid_index, -1, -1):
            self.c0_i[index_of_variable] = indep_var_series_single[j]
            self.equilibrate()
            ceq_series[j, :] = self.ceq_i.T
            xieq_series[j, :] = self.xieq_i.T
        self.ceq_i = self.stored_solution_ceq_i
        self.xieq_i = self.stored_solution_xieq_i
        for j in range(mid_index + 1, n_points + 1, +1):
            self.c0_i[index_of_variable] = indep_var_series_single[j]
            self.equilibrate()
            ceq_series[j, :] = self.ceq_i.T
            xieq_series[j, :] = self.xieq_i.T
        for j in range(n):
            dep_var_series[dep_var_labels[j]] = ceq_series[:, j]
        for j in range(nr):
            dep_var_series[dep_var_labels[n + j]] = xieq_series[:, j]
        self.ceq_i = self.stored_solution_ceq_i
        self.xieq_i = self.stored_solution_xieq_i
        self.Ceq_series = ceq_series
        self.Xieq_series = xieq_series
        self.indep_var_series = indep_var_series
        self.dep_var_series = dep_var_series
        self.dep_var_labels = dep_var_labels
        self.indep_var_label = indep_var_label
        self.index_of_variable = index_of_variable
        self.initiate_plot()

    def initiate_plot(self):
        n = self.n
        nr = self.nr
        dep_var_labels = self.dep_var_labels
        labels_to_plot = [x for x in self.dep_var_labels if x.find('Ceq') >= 0]
        # dict, keys:ceq_labels; bindings: plottedseries
        plotted_series = dict(
            zip(dep_var_labels, np.empty(n + nr, dtype=object)))
        dep_var_labels = self.dep_var_labels
        dep_var_series = self.dep_var_series
        indep_var_series = self.indep_var_series
        indep_var_label = self.indep_var_label
        self.groupBox = QtGui.QGroupBox()
        self.groupBox.plotBox = UiGroupBoxPlot(self.groupBox)
        self.groupBox.plotBox.set_variables(
            plotted_series=plotted_series,
            dep_var_series=dep_var_series,
            dep_var_labels=dep_var_labels,
            dep_var_labels_to_plot=labels_to_plot,
            indep_var_label=indep_var_label,
            indep_var_series=indep_var_series,
            add_path_arrows=False)
        self.groupBox.show()
        self.groupBox.plotBox.plot_intervals(labels_to_plot)

    def recalculate_after_cell_edit(self, row, column):
        self.load_variables_from_form()
        self.gui_equilibrate()

    def gui_equilibrate(self):
        if self.groupBox is not None:
            self.groupBox.hide()  # would need to refresh plotBox or logBox
        self.tableComps.blockSignals(True)
        self.tableReacs.blockSignals(True)
        self.comboBox.blockSignals(True)
        self.gui_setup_and_variables()
        self.equilibrate()
        self.retabulate()

        self.tableComps.blockSignals(False)
        self.tableReacs.blockSignals(False)
        self.comboBox.blockSignals(False)

    def equilibrate(self):
        # Collect variables
        n = self.n
        nr = self.nr
        c0_i = self.c0_i
        z_i = self.z_i
        comps = self.comps
        reacs = self.reacs
        nu_ij = self.nu_ij
        pka_j = self.pka_j
        max_it = self.max_it
        tol = self.tol
        c_solvent_tref = self.c_solvent_tref
        index_of_solvent = self.index_of_solvent

        # Init. calculations
        kc_j = np.multiply(
            np.power(10, -pka_j), np.power(c_solvent_tref, nu_ij[index_of_solvent, :]).T)
        self.kc_j = kc_j

        # Setup logging
        if not os.path.exists('./logs'):
            os.mkdir('./logs')
        logging.basicConfig(
            filename='./logs/calculation_results.log',
            level=logging.DEBUG,
            format='%(asctime)s;%(message)s')

        # First estimates for eq. Composition Ceq and Reaction extent Xieq
        if not hasattr(self, 'acceptable_solution'):
            ceq_i_0 = c0_i
            # replace 0 by 10^-6*smallest value: Smith, Missen 1988 DOI:
            # 10.1002/cjce.5450660409
            ceq_i_0[c0_i == 0] = min(c0_i[c0_i != 0].A1) * np.finfo(float).eps
            xieq_i_0 = np.matrix(np.zeros([nr, 1]))
        else:
            # Use previous solution as initial estimate, if it was valid.
            ceq_i_0 = self.ceq_i_0
            xieq_i_0 = self.xieq_i_0

        # Pass variables to self before loop start
        variables_to_pass = ['c0_i', 'z_i', 'nu_ij', 'pka_j',
                             'max_it', 'tol',
                             'ceq_i_0', 'xieq_i_0']
        for var in variables_to_pass:
            setattr(self, var, locals()[var])

        k = 1
        stop = False
        self.cancelButton.setEnabled(True)
        self.progress_var.setEnabled(True)
        self.remove_canceled_status()
        self.acceptable_solution = False
        self.initialEstimateAttempts = 1
        self.methodLoops = [0, 0]  # loop numbers: [Line search, Newton]
        # Calculate equilibrium composition: Newton method
        # TODO: Implement global homotopy-continuation method
        while not self.acceptable_solution \
                and k < max_it and stop is False \
                and not self.was_canceled():
            ceq_i, xieq_i = calc_xieq(self)
            k += 1
            # TODO: if progress_var.wasCanceled() == True then stop
            if all(ceq_i >= 0) and not any(np.isnan(ceq_i)):
                self.acceptable_solution = True
            else:
                # Set reactions to random extent and recalculate
                # TODO: scale to concentration sizes
                self.xieq_i_0 = np.matrix(
                    np.random.normal(0.0, 1.0 / 3.0, nr)).T
                # Set aequilibrium composition to initial value + estimated
                # conversion
                self.ceq_i_0 = c0_i  # + nu_ij * self.xieq_i_0
                # replace 0 by 10^-6*smallest value: Smith, Missen 1988 DOI:
                # 10.1002/cjce.5450660409
                self.ceq_i_0[self.ceq_i_0 == 0] = min(
                    c0_i[c0_i != 0].A1) * np.finfo(float).eps
                self.initialEstimateAttempts += 1
                self.methodLoops = [0, 0]

        if not self.acceptable_solution:
            delattr(self, 'acceptable_solution')
            self.label_9.setText(self.label_9.text() + '\n')
        else:
            self.ceq_i_0 = ceq_i
            self.xieq_i_0 = xieq_i
            self.label_9.setText(self.label_9.text() +
                                 '\nsum(C0*z_i) = ' + str((z_i.T * c0_i).item()) +
                                 ' \t\t\t sum(Ceq_i*z_i) = ' + str((z_i.T * ceq_i).item()) +
                                 '\nI_0 = ' + str((1 / 2.0 * np.power(z_i, 2).T * c0_i).item()) +
                                 '\t\t\t\t I_eq = ' + str((1 / 2.0 * np.power(z_i, 2).T * ceq_i).item()))

        self.ceq_i = ceq_i
        self.xieq_i = xieq_i
        self.cancelButton.setEnabled(False)
        self.progress_var.setEnabled(False)

    def display_about_info(self):
        row_string = unicode('', 'utf_8')
        self.aboutBox_1 = QtGui.QTextBrowser()
        self.aboutBox_1.setWindowTitle('About')
        self.aboutBox_1.setWindowIcon(QtGui.QIcon(
            os.path.join(sys.path[0], *['utils', 'icon_batch.png'])))
        self.aboutBox_1.setOpenExternalLinks(True)
        adding_table = False

        html_stream = unicode(
            '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">\n',
            'utf_8')
        html_stream += unicode('<html>', 'utf_8')
        html_stream += unicode(
            '<head><meta name="qrichtext" content="1" /><style type="text/css">' +
            '\\np,li {white-space: pre-wrap;}\n' +
            '\\np,br {line-height: 10%;}\n' +
            '</style></head>',
            'utf_8')

        html_stream += unicode('<body style=' +
                               '"' +
                               ' font-family:' +
                               "'" +
                               'MS Shell Dlg 2' +
                               "'" +
                               '; font-size:8.25pt; font-weight:400; font-style:normal;' +
                               '"' +
                               '>', 'utf_8')
        string_to_add = unicode('', 'utf_8')
        starting_p = unicode(
            "<p style=' margin-top:0px; margin-bottom:0px; margin-left:0px;" +
            "margin-right:0px; -qt-block-indent:0; text-indent:0px;'>",
            'utf_8')
        ending_p = unicode('</p>', 'utf_8')
        with open('README.md') as readme_file:
            for row in readme_file:
                row_string = unicode(row, 'utf_8')
                if not adding_table and row_string.find('|') != -1:
                    string_to_add = ''.join(
                        ['<table>', '<tr><td>',
                         row_string.replace('|', '</td><td>').replace('\n', ''),
                         '</td></tr>'])
                    adding_table = True
                elif adding_table and row_string.find('|') == -1:
                    string_to_add = '</table>' + starting_p + row_string + ending_p
                    adding_table = False
                elif adding_table and row_string.find('|') != -1:
                    string_to_add = ''.join(['<tr><td>', row_string.replace(
                        '|', '</td><td>').replace('\n', ''), '</td></tr>'])
                elif not adding_table and row_string.find('|') == -1:
                    string_to_add = starting_p + row_string + ending_p
                if len(row_string.replace('\n', '')) == 0:
                    html_stream += string_to_add + '<br>'
                elif matchingHLine.match(row_string):
                    html_stream += '<hr />'
                else:
                    html_stream += string_to_add
        html_stream += unicode('<hr />', 'utf_8')
        html_stream += unicode(
            "<footer><p>" +
            '<a href=' +
            '"' +
            'https://github.com/santiago-salas-v/lit-impl-py' +
            '"' +
            '>' +
            'https://github.com/santiago-salas-v/lit-impl-py</a></p></footer>',
            'utf_8')
        html_stream += unicode('</body></html>', 'utf_8')
        readme_file.close()
        self.aboutBox_1.setHtml(html_stream)
        self.aboutBox_1.setMinimumWidth(500)
        self.aboutBox_1.setMinimumHeight(400)
        self.aboutBox_1.show()

    def show_log(self):
        headers_and_types = np.array(
            (('date', str),
             ('method', str),
             ('k', int),
             ('backtrack', int),
             ('lambda_ls', float),
             ('accum_step', float),
             ('X', list),
             ('||X(k)-X(k-1)||', float),
             ('f(X)', list),
             ('||f(X)||', float),
             ('Y', list),
             ('||Y||', float),
             ('g', float),
             ('|g-g1|', float),
             ('stop', bool),
             ('series_id', str)))

        headers_and_types_dict = dict(headers_and_types)
        col_numbers_with_float = \
            np.argwhere(map(lambda x: x == float, headers_and_types[:, 1]))
        col_numbers_with_list = \
            np.argwhere(map(lambda x: x == list, headers_and_types[:, 1]))
        col_numbers_with_int = \
            np.argwhere(map(lambda x: x == int, headers_and_types[:, 1]))
        col_numbers_with_str = \
            np.argwhere(map(lambda x: x == str, headers_and_types[:, 1]))
        col_numbers_with_bool = \
            np.argwhere(map(lambda x: x == bool, headers_and_types[:, 1]))

        cell_conversions = dict.fromkeys(headers_and_types_dict.keys())

        for i in range(len(headers_and_types)):
            if i == 0:
                cell_conversions[headers_and_types[i, 0]] = take_date
            elif i in col_numbers_with_float:
                cell_conversions[headers_and_types[i, 0]] = take_float
            elif i in col_numbers_with_list:
                cell_conversions[headers_and_types[i, 0]] = take_list
            elif i in col_numbers_with_int:
                cell_conversions[headers_and_types[i, 0]] = take_int
            elif i in col_numbers_with_bool:
                cell_conversions[headers_and_types[i, 0]] = take_bool
            elif i in col_numbers_with_str:
                pass
            i += 1

        log = pd.read_csv(
            filepath_or_buffer='./logs/calculation_results.log',
            delimiter=';',
            names=headers_and_types[:, 0],
            index_col=False,
            converters=cell_conversions)
        self.groupBox = QtGui.QGroupBox()
        self.groupBox.log_widget = LogWidget(log, parent=self.groupBox)
        self.groupBox.show()


class UiGroupBoxPlot(QtGui.QWidget):

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        # Default size
        parent.resize(741, 421)
        # Assignments
        log_scale_func_list = [
            ('-log10', lambda x: -1.0 * np.log10(x)), ('', lambda x: 10.0 ** (-1.0 * x))]
        self.icon_down = QtGui.QIcon(os.path.join(
            sys.path[0], *['utils', 'glyphicons-602-chevron-down.png']))
        self.icon_up = QtGui.QIcon(os.path.join(
            sys.path[0], *['utils', 'glyphicons-601-chevron-up.png']))
        self.verticalLayout_1 = QtGui.QVBoxLayout(parent)
        self.horizontalTools = QtGui.QHBoxLayout()
        self.toolsFrame = QtGui.QFrame()
        self.toggleLogButtonX = QtGui.QPushButton()
        self.toggleLogButtonY = QtGui.QPushButton()
        self.eraseAnnotationsB = QtGui.QPushButton()
        self.navigation_frame = QtGui.QFrame()
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.figure = Figure(dpi=72, facecolor=(1, 1, 1),
                             edgecolor=(0, 0, 0))
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.label = QtGui.QLabel(parent)
        self.listWidget_2 = QtGui.QListWidget(parent)
        self.label_2 = QtGui.QLabel(parent)
        self.listWidget = QtGui.QListWidget(parent)
        self.plotButton = QtGui.QPushButton(parent)
        self.toolbar = NavigationToolbar(self.canvas, self.navigation_frame)
        self.horizontalLayout_1 = QtGui.QHBoxLayout()
        self.all_to_displayed = QtGui.QPushButton()
        self.all_to_available = QtGui.QPushButton()
        # Default log_log_scale_func_list
        self.set_log_scale_func_list(log_scale_func_list)
        # Object names
        self.verticalLayout_1.setObjectName("verticalLayout_1")
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.canvas.setObjectName("canvas")
        self.verticalLayout.setObjectName("verticalLayout")
        self.label.setObjectName("label")
        self.listWidget_2.setObjectName("listWidget_2")
        self.label_2.setObjectName("label_2")
        self.listWidget.setObjectName("listWidget")
        self.plotButton.setObjectName("plotButton")
        # Operations
        self.eraseAnnotationsB.setIcon(QtGui.QIcon(os.path.join(
            sys.path[0], *['utils', 'glyphicons-551-erase.png'])))
        self.figure.subplots_adjust(bottom=0.15)
        self.ax.grid('on')
        self.horizontalLayout.addWidget(self.canvas)
        self.verticalLayout_1.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalTools.setContentsMargins(0, 0, 0, 0)
        self.horizontalTools.setAlignment(QtCore.Qt.AlignVCenter)
        self.toolsFrame.setLayout(self.horizontalTools)
        self.toggleLogButtonX.setCheckable(True)
        self.toggleLogButtonY.setCheckable(True)
        self.verticalLayout_1.addWidget(self.navigation_frame)
        self.horizontalTools.addWidget(self.toggleLogButtonY)
        self.horizontalTools.addWidget(self.toggleLogButtonX)
        self.horizontalTools.addWidget(self.eraseAnnotationsB)
        self.verticalLayout_1.addWidget(self.toolsFrame)
        self.verticalLayout_1.addLayout(self.horizontalLayout)
        self.listWidget_2.setSelectionMode(
            QtGui.QAbstractItemView.MultiSelection)
        self.listWidget.setSelectionMode(
            QtGui.QAbstractItemView.MultiSelection)
        self.listWidget_2.setViewMode(QtGui.QListView.ListMode)
        self.listWidget_2.setSortingEnabled(True)
        self.listWidget.setSortingEnabled(True)
        self.verticalLayout.addWidget(self.label)
        self.verticalLayout.addWidget(self.listWidget_2)
        self.verticalLayout.addLayout(self.horizontalLayout_1)
        self.all_to_displayed.setIcon(self.icon_up)
        self.all_to_available.setIcon(self.icon_down)
        self.horizontalLayout_1.addWidget(self.all_to_available)
        self.horizontalLayout_1.addWidget(self.all_to_displayed)
        self.verticalLayout.addWidget(self.label_2)
        self.verticalLayout.addWidget(self.listWidget)
        self.verticalLayout.addWidget(self.plotButton)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.navigation_frame.setMinimumHeight(self.toolbar.height())
        # Events
        self.listWidget_2.itemDoubleClicked.connect(
            partial(self.move_to_available))
        self.listWidget.itemDoubleClicked.connect(
            partial(self.move_to_displayed))
        # self.all_to_available.clicked.connect(
        #    partial(self.move_to_available(self.listWidget_2.items)))
        self.toggleLogButtonX.toggled.connect(
            partial(self.toggled_toggle_log_button_x))
        self.toggleLogButtonY.toggled.connect(
            partial(self.toggled_toggle_log_button_y))
        self.eraseAnnotationsB.clicked.connect(partial(self.erase_annotations))
        self.plotButton.clicked.connect(partial(self.force_update_plot))
        # Retranslate, connect
        self.retranslate_ui(parent)
        QtCore.QMetaObject.connectSlotsByName(parent)

    def set_variables(
            self,
            plotted_series,
            dep_var_series,
            dep_var_labels,
            indep_var_label,
            indep_var_series,
            dep_var_labels_to_plot=None,
            log_x_checked=True,
            log_y_checked=True,
            log_scale_func_list=None,
            add_path_arrows=False):
        self.toggleLogButtonX.blockSignals(True)
        self.toggleLogButtonY.blockSignals(True)
        self.toggleLogButtonX.setChecked(log_x_checked)
        self.toggleLogButtonY.setChecked(log_y_checked)
        self.toggleLogButtonX.blockSignals(False)
        self.toggleLogButtonY.blockSignals(False)

        # Variables to be set
        self.dc = dict()  # space to store data cursors for each series
        self.plotted_series = plotted_series
        self.dep_var_series = dep_var_series
        self.dep_var_labels = dep_var_labels
        self.indep_var_label = indep_var_label
        self.indep_var_series = indep_var_series
        self.log_x_checked = log_x_checked
        self.log_y_checked = log_y_checked
        self.log_scale_func_list = log_scale_func_list
        self.log_dep_var_series = dict.fromkeys(dep_var_series.keys())
        self.log_indep_var_series = dict.fromkeys(indep_var_series.keys())
        self.add_path_arrows = add_path_arrows
        # Default log scale to -log10, but enable use of other log scales depending on setting of this array.
        # Form:
        # [(log_scale_string,log_scale_func),(invlog_scale_string,invlog_scale_func)]
        if log_scale_func_list is None:
            pass
        else:
            self.set_log_scale_func_list(log_scale_func_list)
        # Variabeln in Log-Skala
        for k in self.log_dep_var_series.iterkeys():
            self.log_dep_var_series[k] = \
                self.log_scale_func(self.dep_var_series[k])
            self.log_indep_var_series[k] = \
                self.log_scale_func(self.indep_var_series[k])
        # Populate lists with displayed / available functions
        for label in dep_var_labels:
            if label in dep_var_labels_to_plot:
                new_item = QtGui.QListWidgetItem(label, self.listWidget_2)
                new_item.setIcon(self.icon_down)
            else:
                new_item = QtGui.QListWidgetItem(label, self.listWidget)
                new_item.setIcon(self.icon_up)

    def force_update_plot(self):
        ylabel = self.ax.get_ylabel()
        self.ax.clear()
        self.ax.grid('on')
        self.plot_intervals()
        self.ax.set_ylabel(ylabel)

    def set_log_scale_func_list(self, log_scale_func_list):
        self.log_scale_string = log_scale_func_list[0][0]
        self.log_scale_func = log_scale_func_list[0][1]
        self.invlog_scale_string = log_scale_func_list[1][0]
        self.invlog_scale_func = log_scale_func_list[1][1]
        self.find_log_variable = re.compile(
            '\$?(?P<log>' +
            self.log_scale_string +
            '\()(?P<id>[^\$]*)(\))\$?|\$?(?P<id2>[^\$]*)\$?')
        self.toggleLogButtonX.setText(
            self.log_scale_string + "(x) - horizontal")
        self.toggleLogButtonY.setText(self.log_scale_string + "(y) - vertical")

    def retranslate_ui(self, parent):
        parent.setWindowTitle(
            QtGui.QApplication.translate(
                "parent",
                "Plot",
                None,
                QtGui.QApplication.UnicodeUTF8))
        parent.setTitle(
            QtGui.QApplication.translate(
                "parent",
                "Plot",
                None,
                QtGui.QApplication.UnicodeUTF8))
        self.label.setText(
            QtGui.QApplication.translate(
                "parent",
                "Displayed",
                None,
                QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(
            QtGui.QApplication.translate(
                "parent",
                "Available",
                None,
                QtGui.QApplication.UnicodeUTF8))
        self.plotButton.setText(
            QtGui.QApplication.translate(
                "parent",
                "Plot",
                None,
                QtGui.QApplication.UnicodeUTF8))
        self.toggleLogButtonX.setText(
            QtGui.QApplication.translate(
                "parent",
                self.log_scale_string +
                "(x) - horizontal",
                None,
                QtGui.QApplication.UnicodeUTF8))
        self.toggleLogButtonY.setText(
            QtGui.QApplication.translate(
                "parent",
                self.log_scale_string +
                "(y) - vertical",
                None,
                QtGui.QApplication.UnicodeUTF8))
        self.eraseAnnotationsB.setText(
            QtGui.QApplication.translate(
                "parent",
                "Erase annotations",
                None,
                QtGui.QApplication.UnicodeUTF8))
        self.all_to_available.setText(
            QtGui.QApplication.translate(
                "parent",
                "All",
                None,
                QtGui.QApplication.UnicodeUTF8))
        self.all_to_displayed.setText(
            QtGui.QApplication.translate(
                "parent",
                "All",
                None,
                QtGui.QApplication.UnicodeUTF8))

    def toggled_toggle_log_button_x(self, checked):
        self.delete_arrows()
        match = self.find_log_variable.search(self.ax.get_xlabel())
        for line in self.ax.lines:
            line_xdata = line.get_xdata()
            line_label_match = self.find_log_variable.search(line.get_label())
            line_label = line_label_match.group('id')
            if line_label is None:
                line_label = line_label_match.group('id2')
            if not checked and (
                    match.group('log') is not None):  # just unchecked
                if line_label in self.indep_var_series.keys():
                    line.set_xdata(self.indep_var_series[line_label])
                else:
                    line.set_xdata(self.invlog_scale_func(line_xdata))
                self.ax.set_xlabel(u'$' + match.group('id') + u'$')
            else:  # just checked
                if line_label in self.indep_var_series.keys():
                    line.set_xdata(self.log_indep_var_series[line_label])
                else:
                    # TODO: Check first if any data are nan due to conversion.
                    line.set_xdata(self.log_scale_func(line_xdata))
                self.ax.set_xlabel(
                    '$' + self.log_scale_string + '(' + match.group('id2') + ')' + '$')
        if self.add_path_arrows:
            add_arrow_to_line2d(
                self.ax,
                self.ax.get_lines(),
                arrow_locs=np.linspace(
                    0.,
                    1.,
                    15),
                arrow_style='->',
                arrow_size=2)
        self.ax.legend(
            loc='best',
            fancybox=True,
            borderaxespad=0.,
            framealpha=0.5).draggable(True)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

    def toggled_toggle_log_button_y(self, checked):
        self.delete_arrows()
        for line in self.ax.lines:
            line_label = line.get_label()
            line_ydata = line.get_ydata()
            match = self.find_log_variable.search(line_label)
            if not checked and (match.group('log') is not None):
                if match.group('id') in self.dep_var_series.keys():
                    line.set_ydata(
                        self.dep_var_series[
                            match.group('id')].A1.tolist())
                else:
                    line.set_ydata(self.invlog_scale_func(line_ydata))
                line.set_label(u'$' + match.group('id') + u'$')
            else:
                if match.group('id2') in self.dep_var_series.keys():
                    line.set_ydata(
                        self.log_dep_var_series[
                            match.group('id2')].A1.tolist())
                else:
                    # TODO: Check first if any data are nan due to conversion.
                    line.set_ydata(self.invlog_scale_func(line_ydata))
                line.set_label('$' + self.log_scale_string +
                               '(' + match.group('id2') + ')' + '$')
        if self.add_path_arrows:
            add_arrow_to_line2d(
                self.ax,
                self.ax.get_lines(),
                arrow_locs=np.linspace(
                    0.,
                    1.,
                    15),
                arrow_style='->',
                arrow_size=2)
        self.ax.legend(
            loc='best',
            fancybox=True,
            borderaxespad=0.,
            framealpha=0.5).draggable(True)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

    def plot_intervals(self, item_texts=None):
        self.erase_annotations()
        self.delete_arrows()
        plotted_series = self.plotted_series
        dc = dict(zip(self.dep_var_labels, np.empty(len(self.dep_var_labels))))
        if item_texts is None:
            item_texts = []
            for i in range(self.listWidget_2.count()):
                item_texts.append(self.listWidget_2.item(i).text())
        # Nur die Linien hinzufügen, die noch nicht aufgezeichnet wurden.
        done_series = []
        series_to_plot = []
        for x in self.ax.get_lines():
            match = self.find_log_variable.search(x.get_label())
            if match is not None and match.group('id') is not None:
                done_series.append(match.group('id'))
            elif match is not None and match.group('id2') is not None:
                done_series.append(match.group('id2'))
        for x in item_texts:
            if x not in done_series:
                series_to_plot.append(x)
        if not self.toggleLogButtonX.isChecked():
            indep_var_label = '$' + self.indep_var_label + '$'
        else:
            indep_var_label = '$' + self.log_scale_string + \
                              '(' + self.indep_var_label + ')$'
        for label in series_to_plot:
            if not self.toggleLogButtonX.isChecked():
                indep_var_values = self.indep_var_series[label]
            else:
                indep_var_values = self.log_indep_var_series[label]
            if not self.toggleLogButtonY.isChecked():
                dep_var_values = self.dep_var_series[label]
                series_label = '$' + label + '$'
            else:
                dep_var_values = self.log_dep_var_series[label]
                series_label = '$' + self.log_scale_string + '(' + label + ')$'
            plotted_series[label] = self.ax.plot(
                indep_var_values, dep_var_values.A1.tolist(), 'go-', label=series_label,
                color=colormap_colors[np.random.randint(0, len(colormap_colors), 1)],
                markerfacecolor=colormap_colors[np.random.randint(0, len(colormap_colors), 1)],
                marker=markers[np.random.randint(0, len(markers) - 1)],
                fillstyle=fillstyles[np.random.randint(0, len(fillstyles) - 1)])
            dc[label] = datacursor(
                plotted_series[label], draggable=True, display='multiple', arrowprops=dict(
                    arrowstyle='simple', fc='white', alpha=0.5), bbox=dict(
                    fc='white', alpha=0.5), formatter='x: {x:0.3g},y: {y:0.3g}\n{label}'.format)
        if self.add_path_arrows:
            add_arrow_to_line2d(
                self.ax,
                self.ax.get_lines(),
                arrow_locs=np.linspace(
                    0.,
                    1.,
                    15),
                arrow_style='->',
                arrow_size=2)
        self.ax.legend(
            loc='best',
            fancybox=True,
            borderaxespad=0.,
            framealpha=0.5).draggable(True)
        self.plotted_series = plotted_series
        self.dc = dc
        self.ax.set_xlabel(indep_var_label, fontsize=14)
        self.listWidget_2.setMinimumWidth(
            self.listWidget_2.sizeHintForColumn(0))
        self.canvas.draw()

    def erase_annotations(self, text_list=None):
        if text_list is None:
            text_list = [x.get_text() for x in self.figure.texts]
        for text in text_list:
            indexes_of_text = np.where(
                [x.get_text().find(text) >= 0 for x in self.figure.texts])[0]
            if len(indexes_of_text) > 1:
                l = self.figure.texts.pop(indexes_of_text[0].item())
                del l
            else:
                l = self.figure.texts.pop(indexes_of_text.item())
                del l
        self.canvas.draw()

    def move_to_available(self, item):
        self.delete_arrows()
        if self.listWidget_2.count() <= 1:
            return
        selected_items = self.listWidget_2.selectedItems()
        for selected_item in selected_items:
            name = selected_item.text()
            new_item = self.listWidget_2.takeItem(
                self.listWidget_2.indexFromItem(selected_item).row())
            new_item.setIcon(QtGui.QIcon(os.path.join(
                sys.path[0], *['utils', 'glyphicons-601-chevron-up.png'])))
            self.listWidget.insertItem(self.listWidget.count(), new_item)
            associated_annotations = [
                x.get_text() for x in self.figure.texts if x.get_text().find(name) >= 0]
            self.erase_annotations(associated_annotations)
            l = self.ax.lines.pop(np.where(
                [x.properties()['label'].find(name) >= 0 for x in self.ax.lines])[0].item())
            del l
        if len(self.ax.lines) > 0:
            self.ax.legend(
                loc='best',
                fancybox=True,
                borderaxespad=0.,
                framealpha=0.5).draggable(True)
        else:
            del self.ax.legend
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

    def move_to_displayed(self, item):
        self.delete_arrows()
        selected_items = self.listWidget.selectedItems()
        selected_items_names = [x.text() for x in selected_items]
        for selected_item in selected_items:
            name = item.text()
            new_item = self.listWidget.takeItem(
                self.listWidget.indexFromItem(selected_item).row())
            new_item.setIcon(QtGui.QIcon(os.path.join(
                sys.path[0], *['utils', 'glyphicons-602-chevron-down.png'])))
            self.listWidget_2.insertItem(self.listWidget_2.count(), new_item)
        self.plot_intervals(selected_items_names)
        if len(self.ax.lines) > 0:
            self.ax.legend(
                loc='best',
                fancybox=True,
                borderaxespad=0.,
                framealpha=0.5).draggable(True)
        else:
            del self.ax.legend
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

    def clear_all(self):
        self.ax.clear()
        self.listWidget.clear()
        self.listWidget_2.clear()

    def delete_arrows(self):
        while self.ax.patches:
            l = self.ax.patches.pop(0)
            del l


class LogWidget(QtGui.QWidget):

    def __init__(self, _log, parent):
        QtGui.QWidget.__init__(self, parent)
        self.log = _log
        self.icon = QtGui.QIcon()
        self.icon.addPixmap(QtGui.QPixmap(
            _fromutf8("utils/glyphicons-88-log-book.png")),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        parent.setWindowIcon(self.icon)
        self.setup_ui(parent)

    def setup_ui(self, parent):
        # Default size
        self.minLogHeight = 400
        self.minLogWidth = self.minLogHeight * 16 / 9
        parent.resize(self.minLogWidth, self.minLogHeight)
        # Assignments
        self.verticalLayout = QtGui.QVBoxLayout(parent)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.pandasView = QtGui.QTableView()
        self.firstButton = QtGui.QPushButton()
        self.lastButton = QtGui.QPushButton()
        self.nextButton = QtGui.QPushButton()
        self.previousButton = QtGui.QPushButton()
        self.pageLabel = QtGui.QLabel()
        self.totPagesLabel = QtGui.QLabel()
        self.page_box = QtGui.QLineEdit()
        self.exportButton = QtGui.QPushButton()
        self.plotButton = QtGui.QPushButton()
        self.display_items_by_page = 50
        self.current_page_first_entry = len(self.log.values) \
            - self.display_items_by_page
        # Operations
        parent.setWindowTitle('calculation log')
        self.firstButton.setText('<< First')
        self.lastButton.setText('Last >>')
        self.previousButton.setText('< Previous')
        self.nextButton.setText('Next >')
        self.page_box.setMaximumWidth(int(round(self.minLogHeight / float(5))))
        self.page_box.setAlignment(
            QtCore.Qt.AlignHCenter | QtCore.Qt.AlignCenter)
        self.exportButton.setText('Export (csv)')
        self.plotButton.setText('Plot solution paths')
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout.addWidget(self.pandasView)
        self.verticalLayout.addWidget(self.exportButton)
        self.verticalLayout.addWidget(self.plotButton)
        self.horizontalLayout.addWidget(self.firstButton)
        self.horizontalLayout.addWidget(self.previousButton)
        self.horizontalLayout.addWidget(self.pageLabel)
        self.horizontalLayout.addWidget(self.page_box)
        self.horizontalLayout.addWidget(self.totPagesLabel)
        self.horizontalLayout.addWidget(self.nextButton)
        self.horizontalLayout.addWidget(self.lastButton)

        # To ensure full display, first set resize modes, then resize columns
        # to contents
        self.pandasView.horizontalHeader().setResizeMode(QtGui.QHeaderView.Interactive)
        self.pandasView.verticalHeader().setResizeMode(
            QtGui.QHeaderView.ResizeToContents)
        self.pandasView.setWordWrap(True)
        self.pandasView.resizeColumnsToContents()

        # Events
        self.firstButton.clicked.connect(partial(self.first_page))
        self.lastButton.clicked.connect(partial(self.last_page))
        self.nextButton.clicked.connect(partial(self.next_page))
        self.previousButton.clicked.connect(partial(self.previous_page))
        self.exportButton.clicked.connect(partial(self.export_data))
        self.plotButton.clicked.connect(partial(self.plot_data))
        self.page_box.editingFinished.connect(partial(self.go_to_page_no))
        # Display
        self.display()

    def first_page(self):
        self.current_page_first_entry = 0
        self.display_items_by_page = self.display_items_by_page
        self.display()

    def last_page(self):
        self.current_page_first_entry = len(self.log.values) \
            - self.display_items_by_page
        self.display()

    def next_page(self):
        if self.currentPageLastEntry + \
                self.display_items_by_page > len(self.log.values):
            self.current_page_first_entry = len(self.log.values) \
                - self.display_items_by_page
        else:
            self.current_page_first_entry = self.current_page_first_entry + \
                self.display_items_by_page
        self.display()

    def previous_page(self):
        if self.current_page_first_entry - \
                self.display_items_by_page < 0:
            self.current_page_first_entry = 0
        else:
            self.current_page_first_entry = self.current_page_first_entry - \
                self.display_items_by_page
        self.display()

    def go_to_page_no(self):
        page_text = self.page_box.text()
        try:
            page_no = int(round(float(page_text)))
            self.last_page = int(round(len(self.log.values) /
                                       float(self.display_items_by_page)))
            if page_no < self.last_page:
                self.current_page_first_entry = \
                    (page_no - 1) * self.display_items_by_page + 1
            elif page_no >= self.last_page:
                self.current_page_first_entry = len(self.log.values) \
                    - self.display_items_by_page
            elif page_no <= 1:
                self.current_page_first_entry = 1
            self.display()
        except ValueError:
            pass

    def display(self):
        # Page number
        self.currentPageLastEntry = self.current_page_first_entry + \
            self.display_items_by_page
        self.currentPage = int(round(self.currentPageLastEntry /
                                     float(self.display_items_by_page)))
        self.last_page = int(round(len(self.log.values) /
                                   float(self.display_items_by_page)))

        self.pandas_model = PandasModel(
            self.log[self.current_page_first_entry: self.currentPageLastEntry])
        self.pandasView.setModel(self.pandas_model)
        self.pandasView.resizeColumnsToContents()
        self.pandasView.verticalHeaders = \
            map(str, range(self.current_page_first_entry,
                           self.currentPageLastEntry + 1, 1))
        self.totPagesLabel.setText(' / ' + str(self.last_page))
        self.pageLabel.setText('Entries ' +
                               str(self.current_page_first_entry) +
                               ' to ' +
                               str(self.currentPageLastEntry) +
                               '; Page: ')
        self.page_box.blockSignals(True)
        self.page_box.setText(str(self.currentPage))
        self.page_box.blockSignals(False)

    def export_data(self):
        supported_filters = ['CSV file (*.csv)']
        # TODO: supported_filters = ['CSV file (*.csv)', 'XLSX (2010) (*.xlsx)',
        # 'XLS (2007) (*.xls)']
        (file_name, selected_filter) = QtGui.QFileDialog.getSaveFileName(
            parent=self.group_2,
            caption='enter file name to save...',
            filter=';;'.join(supported_filters))
        if selected_filter == supported_filters[0]:
            self.log.to_csv(file_name)
            # elif selected_filter == supported_filters[1] or \
            #                selected_filter == supported_filters[2]:
            #    self.log.to_excel(file_name)

    def plot_data(self):
        grouped = self.log.groupby('series_id')
        # dict, keys:ceq_labels; bindings: plottedseries
        dep_var_labels = grouped.head(1)['date'].apply(lambda x: str(x)).values
        indep_var_label = 'accum step'
        dep_var_series = dict(
            zip(dep_var_labels, np.empty(len(dep_var_labels))))
        indep_var_series = dict(
            zip(dep_var_labels, np.empty(len(dep_var_labels))))
        plotted_series = dict(
            zip(dep_var_labels, np.empty(len(dep_var_labels))))
        log_scale_func_list = [
            ('log10', lambda x: +1.0 * np.log10(x)), ('', lambda x: 10.0 ** (+1.0 * x))]

        for name, group in grouped:
            index = group['date'].head(1).apply(lambda x: str(x)).values.item()
            indep_var_series[index] = group['accum_step'].values
            dep_var_series[index] = np.matrix(group['||f(X)||'].values)
        # Generate the plot
        self.group_3 = QtGui.QGroupBox()
        self.plotBox = UiGroupBoxPlot(self.group_3)
        self.plotBox.set_variables(plotted_series=plotted_series,
                                   dep_var_series=dep_var_series,
                                   dep_var_labels=dep_var_labels,
                                   dep_var_labels_to_plot=[dep_var_labels[-1]],
                                   indep_var_label=indep_var_label,
                                   indep_var_series=indep_var_series,
                                   log_x_checked=False, log_y_checked=False,
                                   log_scale_func_list=log_scale_func_list,
                                   add_path_arrows=True)
        self.plotBox.plot_intervals([dep_var_labels[-1]])
        # FIXME: 2 Punkte, Logx ein- und ausschalten
        self.group_3.show()
        self.plotBox.ax.set_ylabel('||f(X)||')


def calc_xieq(form):
    """Steepest descent for good initial estimate, then Newton method for non-linear algebraic system
    :return: tuple with ceq_i, xieq_i, f_0
    :param c0_i: np.matrix (n x 1) - Conc(i, alimentación)
    :param z_i: np.matrix (n x 1) - Carga(i, alimentación)
    :param nu_ij: np.matrix (n x nr) - Coefs. esteq. componente i en reacción j
    :param pka_j: np.matrix (n x 1) - (-1)*log10("Cte." de equilibrio en reacción j) = -log10 kc_j(T)
    :param xieq_i_0: np.matrix (n x 1) - avance de reacción j - estimado inicial
    :param ceq_i_0: np.matrix (n x 1) - Conc(i, equilibrio)
    """
    n = form.n
    nr = form.nr
    c0_i = form.c0_i
    pka_j = form.pka_j
    nu_ij = form.nu_ij
    ceq_i_0 = form.ceq_i_0
    xieq_i_0 = form.xieq_i_0
    max_it = form.max_it
    tol = form.tol
    z_i = form.z_i
    kc_j = form.kc_j

    f = lambda x: f_gl_0(x, c0_i, nu_ij, n, nr, kc_j)
    j = lambda x: jac(x, c0_i, nu_ij, n, nr, kc_j)

    x0 = np.concatenate([ceq_i_0, xieq_i_0])
    x = x0
    # Newton method: G(x) = J(x)^-1 * F(x)
    k = 0
    j_val = j(x)
    f_val = f(x)
    y = np.matrix(np.ones(len(x))).T * tol / (np.sqrt(len(x)) * tol)
    magnitude_f = np.sqrt((f_val.T * f_val).item())
    # Line search variable lambda
    lambda_ls = 0.0
    accum_step = 0.0
    # For progress bar, use log scale to compensate for quadratic convergence
    log10_to_o_max_magnitude_f = np.log10(tol / magnitude_f)
    progress_k = (1.0 - np.log10(tol / magnitude_f) /
                  log10_to_o_max_magnitude_f) * 100.0
    diff = np.matrix(np.empty([len(x), 1]))
    diff.fill(np.nan)
    stop = False
    divergent = False
    # Add progress bar & variable
    form.progress_var.setValue(0)
    update_status_label(form, k, 'solving...' if not stop else 'solved.')
    # Unique identifier for plotting logged solutions
    series_id = str(uuid.uuid1())
    new_log_entry(
        'Newton',
        k,
        0,
        0,
        accum_step,
        x,
        diff,
        f_val,
        0 * y,
        np.nan,
        np.nan,
        stop,
        series_id)
    while k <= max_it and not stop:
        k += 1
        form.methodLoops[1] += 1
        j_it = 0
        lambda_ls = 1.0
        accum_step += lambda_ls
        x_k_m_1 = x
        progress_k_m_1 = progress_k
        y = gausselimination(j_val, -f_val)
        # First attempt without backtracking
        x = x + lambda_ls * y  # FIXME: Autoassignment throws 1001 iterations
        diff = x - x_k_m_1
        j_val = j(x)
        f_val = f(x)
        magnitude_f = np.sqrt((f_val.T * f_val).item())
        new_log_entry(
            'Newton',
            k,
            j_it,
            lambda_ls,
            accum_step,
            x,
            diff,
            f_val,
            lambda_ls * y,
            np.nan,
            np.nan,
            stop,
            series_id)
        if magnitude_f < tol and all(x[0:n] >= 0):
            stop = True  # Procedure successful
            form.progress_var.setValue(100.0)
        else:
            # For progress bar, use log scale to compensate for quadratic
            # convergence
            update_status_label(
                form, k, 'solving...' if not stop else 'solved.')
            progress_k = (1.0 - np.log10(tol / magnitude_f) /
                          log10_to_o_max_magnitude_f) * 100.0
            if np.isnan(magnitude_f) or np.isinf(magnitude_f):
                stop = True  # Divergent method
                divergent = True
                form.progress_var.setValue(
                    (1.0 -
                     np.log10(
                         np.finfo(float).eps) /
                     log10_to_o_max_magnitude_f) *
                    100.0)
            else:
                form.progress_var.setValue(
                    (1.0 -
                     np.log10(
                         tol /
                         magnitude_f) /
                     log10_to_o_max_magnitude_f) *
                    100.0)
            if round(progress_k) == round(progress_k_m_1):
                QtGui.QApplication.processEvents()
                # if form.progress_var.wasCanceled():
                # stop = True
        while j_it <= max_it and not all(x[0:n] >= 0):
            # Backtrack if any conc < 0. Line search method.
            # Ref. http://dx.doi.org/10.1016/j.compchemeng.2013.06.013
            j_it += 1
            lambda_ls = lambda_ls / 2.0
            accum_step += -lambda_ls
            x = x_k_m_1
            progress_k = progress_k_m_1
            x = x + lambda_ls * y
            diff = x - x_k_m_1
            j_val = j(x)
            f_val = f(x)
            new_log_entry(
                'Newton',
                k,
                j_it,
                lambda_ls,
                accum_step,
                x,
                diff,
                f_val,
                lambda_ls * y,
                np.nan,
                np.nan,
                stop,
                series_id)
            form.methodLoops[0] += 1
            update_status_label(
                form, k, 'solving...' if not stop else 'solved.')
    update_status_label(
        form,
        k,
        'solved.' if stop and not divergent else 'solution not found.')
    ceq_i = x[0:n]
    xieq_i = x[n:n + nr]
    return ceq_i, xieq_i


def f_gl_0(x, c0_i, nu_ij, n, nr, kc_j):
    ceq_i = x[0:n, 0]
    xieq_i = x[n:n + nr, 0]
    result = np.matrix(np.empty([n + nr, 1], dtype=float))
    result[0:n] = -ceq_i + c0_i + nu_ij * xieq_i
    result[n:n + nr] = -kc_j + np.prod(np.power(ceq_i, nu_ij), 0).T
    return result


def jac(x, c0_i, nu_ij, n, nr, kc_j):
    ceq_i = x[0:n, 0]
    eins_durch_c = np.diag(np.power(ceq_i, -1).A1, 0)
    quotient = np.diag(np.prod(np.power(ceq_i, nu_ij), 0).A1)
    result = np.matrix(np.zeros([n + nr, n + nr], dtype=float))
    result[0:n, 0:n] = -1 * np.eye(n).astype(float)
    result[0:n, n:n + nr] = nu_ij
    result[n:n + nr, 0:n] = quotient * nu_ij.T * eins_durch_c
    return result


def update_status_label(form, k, solved):
    form.label_9.setText('Loops: Newton \t' +
                         str(form.methodLoops[1]) +
                         ' \t Line search (backtrack) \t' +
                         str(form.methodLoops[0]) +
                         ' \t Initial estimate attempts \t' +
                         str(form.initialEstimateAttempts) +
                         '\n' +
                         'Iteration (k) \t' +
                         str(k) +
                         '\n' +
                         str(solved))


def new_log_entry(
        method,
        k,
        backtrack,
        lambda_ls,
        accum_step,
        x,
        diff,
        f_val,
        y,
        g_min,
        g1,
        stop,
        series_id):
    logging.debug(method + ' ' +
                  ';k=' + str(k) +
                  ';backtrack=' + str(backtrack) +
                  ';lambda_ls=' + str(lambda_ls) +
                  ';accum_step=' + str(accum_step) +
                  ';X=' + '[' + ','.join(map(str, x.T.A1)) + ']' +
                  ';||X(k)-X(k-1)||=' + str((diff.T * diff).item()) +
                  ';f(X)=' + '[' + ','.join(map(str, f_val.T.A1)) + ']' +
                  ';||f(X)||=' + str(np.sqrt((f_val.T * f_val).item())) +
                  ';Y=' + '[' + ','.join(map(str, y.T.A1)) + ']' +
                  ';||Y||=' + str(np.sqrt((y.T * y).item())) +
                  ';g=' + str(g_min) +
                  ';|g-g1|=' + str(abs(g_min - g1)) +
                  ';stop=' + str(stop) +
                  ';' + series_id)


class PandasModel(QtCore.QAbstractTableModel):
    """
    Used to populate a QTableView with the pandas model
    """

    def __init__(self, data, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._data = data

    def rowCount(self, parent=None):
        return len(self._data.values)

    def columnCount(self, parent=None):
        return self._data.columns.size

    def data(self, index, role=QtCore.Qt.DisplayPropertyRole):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                return str(self._data.values[index.row()][index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._data.columns[col]
        # TODO: Implement vertical header indicating row numbers
        return None


class AboutBox(QtGui.QMessageBox):

    def __init__(self, parent=None):
        QtGui.QMessageBox.__init__(self, parent)

    def about(self, title_text, contained_text):
        QtGui.QMessageBox.__init__(self, None)
        self.setText(title_text)
        self.setDetailedText(contained_text)
        self.show()


class NSortableTableWidgetItem(QtGui.QTableWidgetItem):
    # Implement less than (<) for numeric table widget items.

    def __init__(self, text):
        QtGui.QTableWidgetItem.__init__(self, text)

    def __lt__(self, y):
        float_self = float(self.text())
        if np.isnan(float_self):
            return True
        else:
            return float(self.text()) < float(y.text())


class ScientificDoubleSpinBox(QtGui.QDoubleSpinBox):

    def __init__(self, parent=None):
        QtGui.QDoubleSpinBox.__init__(self, parent)
        self.setMinimum(-np.inf)
        self.setMaximum(np.inf)
        self.validator = FloatValidator()
        self.setDecimals(1000)

    def validate(self, text, position):
        return self.validator.validate(text, position)

    def fixup(self, text):
        return self.validator.fixup(text)

    def valueFromText(self, text):
        return float(text)

    def textFromValue(self, value):
        return format_float(value)

    def stepBy(self, steps):
        text = self.cleanText()
        groups = float_re.search(text).groups()
        decimal = float(groups[1])
        decimal += steps
        new_string = "{:g}".format(decimal) + (groups[3] if groups[3] else "")
        self.lineEdit().setText(new_string)


class FloatValidator(QtGui.QValidator):

    def validate(self, string, position):
        if valid_float_string(string):
            return self.State.Acceptable
        if string == "" or string[position - 1] in 'e.-+':
            return self.State.Intermediate
        return self.State.Invalid

    def fixup(self, text):
        match = float_re.search(text)
        return match.groups()[0] if match else ""


def add_arrow_to_line2d(
        axes, line, arrow_locs=[0.2, 0.4, 0.6, 0.8],
        arrow_style='-|>', arrow_size=1, transform=None):
    """
    Add arrows to a matplotlib.lines.Line2D at selected locations.

    Parameters:
    -----------
    axes:
    line: list of 1 Line2D obbject as returned by plot command
    arrow_locs: list of locations where to insert arrows, % of total length
    arrowstyle: style of the arrow
    arrowsize: size of the arrow
    transform: a matplotlib transform instance, default to data coordinates

    Returns:
    --------
    arrows: list of arrows
    """
    if (not (isinstance(line, list)) or not (
            isinstance(line[0], matplotlib.lines.Line2D))):
        raise ValueError("expected a matplotlib.lines.Line2D object")
    x, y = line[0].get_xdata(), line[0].get_ydata()
    finite_indexes = np.bitwise_and(np.isfinite(x), np.isfinite(y))
    x = np.array(x)[finite_indexes]
    y = np.array(y)[finite_indexes]

    if sum(finite_indexes) < 2:
        return

    arrow_kw = dict(arrowstyle=arrow_style, mutation_scale=10 * arrow_size)

    color = line[0].get_color()
    use_multicolor_lines = isinstance(color, np.ndarray)
    if use_multicolor_lines:
        raise NotImplementedError("multicolor lines not supported")
    else:
        arrow_kw['color'] = color

    linewidth = line[0].get_linewidth()
    if isinstance(linewidth, np.ndarray):
        raise NotImplementedError("multiwidth lines not supported")
    else:
        arrow_kw['linewidth'] = linewidth

    if transform is None:
        axes.relim()
        axes.autoscale_view()
        transform = axes.transData

    arrows = []
    for loc in arrow_locs:
        s = np.cumsum(np.sqrt(np.diff(x) ** 2 + np.diff(y) ** 2))
        n = np.searchsorted(s, s[-1] * loc)
        arrow_tail = (x[n], y[n])
        arrow_head = (np.mean(x[n:n + 2]), np.mean(y[n:n + 2]))
        p = matplotlib.patches.FancyArrowPatch(
            arrow_tail, arrow_head, transform=transform,
            **arrow_kw)
        axes.add_patch(p)
        arrows.append(p)
    return arrows


def format_float(value):
    """Modified form of the 'g' format specifier."""
    string = "{:g}".format(value).replace("e+", "e")
    string = re.sub("e(-?)0*(\d+)", r"e\1\2", string)
    return string


def valid_float_string(string):
    match = float_re.search(string)
    return match.groups()[0] == string if match else False


def main():
    app = QtGui.QApplication.instance()  # checks if QApplication already exists
    if not app:  # create QApplication if it doesnt exist
        app = QtGui.QApplication(sys.argv)

    main_form = QtGui.QGroupBox()
    icon = QtGui.QIcon(
        os.path.join(sys.path[0], *['utils', 'icon_batch.png']))
    main_form.setWindowIcon(icon)
    main_form.ui = UiGroupBox(main_form)
    main_form.show()
    main_form.ui.load_csv('./DATA/COMPONENTS_REACTIONS_EX_001.csv')
    main_form.ui.gui_equilibrate()
    main_form.ui.tableComps.sortByColumn(0, QtCore.Qt.AscendingOrder)
    main_form.ui.tableReacs.sortByColumn(0, QtCore.Qt.AscendingOrder)
    app.exec_()


if __name__ == '__main__':
    main()