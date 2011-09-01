# This file is part of the Frescobaldi project, http://www.frescobaldi.org/
#
# Copyright (c) 2011 by Wilbert Berendsen
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# See http://www.gnu.org/licenses/ for more information.

"""
The completer for Frescobaldi.
"""

from __future__ import unicode_literals

import re

from PyQt4.QtGui import QTextCursor

import app
import listmodel
import textformats
import widgets.completer

import ly.words


class Completer(widgets.completer.Completer):
    def __init__(self):
        super(Completer, self).__init__()
        self.setModel(listmodel.ListModel(sorted(
            ly.words.lilypond_keywords + ly.words.lilypond_music_commands),
            display = lambda item: '\\' + item))
        self.setMaxVisibleItems(16)
        self.popup().setMinimumWidth(100)
        app.settingsChanged.connect(self.readSettings)
        self.readSettings()
    
    def readSettings(self):
        self.popup().setFont(textformats.formatData('editor').font)
    
    def completionCursor(self):
        cursor = self.textCursor()
        text = cursor.block().text()[:cursor.position()-cursor.block().position()]
        m = re.search(r'\\[a-z]?[A-Za-z]*$', text)
        if m:
            cursor.setPosition(cursor.block().position() + m.start(), QTextCursor.KeepAnchor)
            return cursor


    