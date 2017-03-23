import os
import re
import codecs
from threading import Timer
import zipfile
try:
    from io import BytesIO
except ImportError:
    from cStringIO import StringIO as BytesIO

from PyQt5.QtCore import QObject, pyqtSignal

import vcs

class GitDiffReaptedTimer(QObject):
    diff_signal = pyqtSignal(list, list, list)

    def __init__(self, mainwindow, interval):
        QObject.__init__(self)
        self._timer      = None
        self._mainwindow = mainwindow
        self.interval    = interval
        self.is_running  = False
        self._current_doc_path = ""
        self._current_doc = ""

    def removeDiffFiles(self):
        if self._current_doc_path:
            os.unlink(self._current_doc_path + ".origin")
            os.unlink(self._current_doc_path + ".cache")

    def setUpDiffFiles(self, path, current_doc, current_doc_path):
        def setUpNewDiffFiles():
            commit = vcs.app_repo._run_git_command(cmd = "rev-parse", gitpath = path,
                                          args = ["HEAD"])
            commit = commit[:-1] # remove '/n'
            output = vcs.app_repo._run_git_command(cmd = "archive", gitpath = path,
                                          args = ["--format=zip", commit, current_doc], encode = False)
            contents = b''
            if output:
                # Extract file contents from zipped archive.
                # The `filelist` contains numberous directories finalized
                # by exactly one file whose content we are interested in.
                archive = zipfile.ZipFile(BytesIO(output))
                contents = archive.read(archive.filelist[-1])
            # Write the content to file
            with open(current_doc_path + ".origin", 'wb') as file:
                 file.write(contents)
            self._current_doc = current_doc
            self._current_doc_path = current_doc_path

        if current_doc == self._current_doc:
            return
        self.removeDiffFiles()
        setUpNewDiffFiles()

    def _run(self):
        self.is_running = False
        self.start()
        self.gitgutterGetLines()


    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.removeDiffFiles()
        self.is_running = False

    def gitgutterGetLines(self):
        def gitDiffContent():
            current_doc = self._mainwindow.currentDocument()
            current_doc_path = current_doc.url().toLocalFile()
            if current_doc_path == "":
                 return ""
            path_list = current_doc_path.split('/')
            git_path = '/'.join(path_list[:-1]) # just for test
            current_doc_name = path_list[-1]

            cache_path = current_doc_path + ".cache"
            with open(cache_path, "wb") as f:
                f.write(current_doc.encodedText())
                f.flush()
                os.fsync(f.fileno())

            self.setUpDiffFiles(git_path, current_doc_name, current_doc_path)
            results = vcs.app_repo.current_diff(path = git_path,
                           origin_file = current_doc_name +".origin",  cache_file = current_doc_name +".cache")
            return results

        def diffProcess():
            diff_str = gitDiffContent()
            if diff_str == "":
                self.diff_signal.emit([], [], [])
                return
            # first and last changed line in the view
            first, last = 0, 0
            # lists with inserted, modified and deleted lines
            inserted, modified, deleted = [], [], []
            hunk_re = r'^@@ \-(\d+),?(\d*) \+(\d+),?(\d*) @@'
            for hunk in re.finditer(hunk_re, diff_str, re.MULTILINE):
                _, old_size, start, new_size = hunk.groups()
                start = int(start)
                old_size = int(old_size or 1)
                new_size = int(new_size or 1)
                if first == 0:
                    first = max(1, start)
                if not old_size:
                    last = start + new_size
                    inserted += range(start, last)
                elif not new_size:
                    last = start + 1
                    deleted.append(last)
                else:
                    last = start + new_size
                    modified += range(start, last)
            self.diff_signal.emit(inserted, modified, deleted)

        return diffProcess()

    def connectSignal(self, fn):
        self.diff_signal.connect(fn)
