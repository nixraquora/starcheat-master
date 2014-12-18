"""
Qt item browser dialog
"""

import logging
from PyQt5.QtWidgets import QDialog, QTableWidgetItem, QDialogButtonBox, QListWidgetItem
from PyQt5.QtGui import QPixmap, QImage
from PIL.ImageQt import ImageQt

import assets, qt_itembrowser
from config import Config

def format_status_effects(data):
    info = "<b>Status Effects:</b><br>"
    for status in data:
        if "amount" in status:
            info += "%s (%s)<br>" % (status["kind"], str(status["amount"]))
        else:
            info += "%s<br>" % status["kind"]
    return info

def format_effects(data):
    info = "<b>Effects:</b><br>"
    for status in data[0]:
        if "amount" in status:
            info += "%s (%s)<br>" % (status["kind"], str(status["amount"]))
        else:
            info += "%s<br>" % status["kind"]
    return info

data_format = (
    # (key name, format/func)
    # key name is name of the key in item data it corresponds to
    # format/func is either a format string with 1 %s replacement that the
    # key gets passed to or a function that outputs a string using the option
    # as input
    # order matters
    ("shortdescription", "<b>%s</b> "),
    ("itemName", "(%s)<br>"),
    ("objectName", "(%s)<br>"),
    ("description", "%s<br><br>"),
    ("inspectionKind", "<b>Type:</b> %s<br>"),
    ("rarity", "<b>Rarity:</b> %s<br><br>"),
    ("statusEffects", format_status_effects),
    ("effects", format_effects),
    ("blockRadius", "<b>Mining Radius:</b> %s blocks")
)

def generate_item_info(item_data):
    """Takes inventory item data and makes a detailed description (HTML)."""
    info = ""

    if item_data == None:
        return ""

    for fmt in data_format:
        if fmt[0] in item_data:
            if type(fmt[1]) is str:
                info += fmt[1] % str(item_data[fmt[0]])
            else:
                info += fmt[1](item_data[fmt[0]])

    return info


class BrowserItem(QListWidgetItem):
    def __init__(self, name, desc):
        if desc == "":
            display = name
        else:
            #display = "%s (%s)" % (desc, name)
            display = desc
        QListWidgetItem.__init__(self, display)
        self.name = name

class ItemBrowser():
    def __init__(self, parent, just_browse=False, category="<all>"):
        """Dialog for viewing/searching indexed items and returning selection."""
        self.dialog = QDialog(parent)
        self.ui = qt_itembrowser.Ui_Dialog()
        self.ui.setupUi(self.dialog)

        assets_db_file = Config().read("assets_db")
        starbound_folder = Config().read("starbound_folder")
        self.assets = assets.Assets(assets_db_file, starbound_folder)

        self.remember_category = category

        if just_browse:
            self.ui.buttonBox.setStandardButtons(QDialogButtonBox.Close)

        self.item_browse_select = None
        self.items = self.assets.items()

        # populate category combobox
        for cat in self.items.get_categories():
            self.ui.category.addItem(cat[0])
        self.ui.category.setCurrentText(self.remember_category)

        # populate initial items list
        self.ui.items.clear()
        self.update_item_list()
        self.update_item_view()

        self.ui.items.itemSelectionChanged.connect(self.update_item_view)
        if not just_browse:
            self.ui.items.itemDoubleClicked.connect(self.dialog.accept)
        self.ui.filter.textChanged.connect(self.update_item_list)
        self.ui.category.currentTextChanged.connect(self.update_item_list)

        self.ui.items.setCurrentRow(0)
        self.ui.filter.setFocus()

    def update_item_view(self):
        """Update item details view with data from currently selected item."""
        try:
            selected = self.ui.items.selectedItems()[0].name
        except IndexError:
            return

        try:
            item = self.items.get_item(selected)
        except TypeError:
            logging.warning("Unable to load asset "+selected)
            return

        image_file = self.items.get_item_image(selected)
        if image_file == None:
            inv_icon_file = self.items.get_item_icon(selected)
            if inv_icon_file != None:
                icon = QPixmap.fromImage(ImageQt(inv_icon_file)).scaled(32, 32)
            else:
                icon = QPixmap.fromImage(QImage.fromData(self.items.missing_icon())).scaled(32, 32)
        else:
            icon = QPixmap.fromImage(ImageQt(image_file)).scaledToHeight(64)

        # last ditch
        try:
            self.ui.item_icon.setPixmap(icon)
        except TypeError:
            logging.warning("Unable to load item image: "+selected)
            self.ui.item_icon.setPixmap(QPixmap())

        self.ui.short_desc.setText(generate_item_info(item[0]))

        # populate default variant table
        row = 0
        self.ui.info.setRowCount(len(item[0]))
        for key in sorted(item[0].keys()):
            try:
                text = str(key) + ": " + str(item[0][key])
                table_item = QTableWidgetItem(text)
                table_item.setToolTip(text)
                self.ui.info.setItem(row, 0, table_item)
            except TypeError:
                pass
            row += 1

        self.item_browse_select = selected

    def update_item_list(self):
        """Populate item list based on current filter details."""
        category = self.ui.category.currentText()
        self.remember_category = category
        name = self.ui.filter.text()
        result = self.items.filter_items(category, name)

        # TODO: i'd like this to set focus on the list when category is changed
        #       but not when the edit box is changed (split this function)
        self.ui.items.clear()
        for item in result:
            self.ui.items.addItem(BrowserItem(item[4], item[5]))
        self.ui.items.setCurrentRow(0)

    def get_selection(self):
        return self.item_browse_select
