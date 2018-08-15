import requests

# create a Session object
# s = requests.Session()

# # first visit the main page
# s.get("http://tuvi.cohoc.net/la-so-tu-vi-co-hoc-lid-17.html")

# # then we can visit the weekly report pages
# r = s.get("http://tuvi.cohoc.net/404.html?ref=cache-not-found&id=17")

# # print(r.text)

# # # another page
# r = s.get("http://tuvi.cohoc.net/la-so-tu-vi-co-hoc-lid-17.html")
# print(r.text)

import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtWebKit import *


class Render(QWebPage):
  def __init__(self, url):
    self.app = QApplication(sys.argv)
    QWebPage.__init__(self)
    self.loadFinished.connect(self._loadFinished)
    self.mainFrame().load(QUrl(url))
    self.app.exec_()

  def _loadFinished(self, result):
    self.frame = self.mainFrame()
    self.app.quit()


url = 'http://tuvi.cohoc.net/la-so-tu-vi-co-hoc-lid-18.html'
r = Render(url)
html = r.frame.toHtml()
