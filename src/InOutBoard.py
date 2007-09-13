
INOUT_URL = "http://calvin/clockwork/index.php"
import urllib
from BeautifulSoup import BeautifulSoup

class InOutBoard:

  def __init__(self, url):
    self.url = url

    # get the post vars from the form: inputs (6), selects (2), textareas (1)
    self.params = {}
    html = urllib.urlopen(self.url + '?go=1').read()
    soup = BeautifulSoup(html)

    for input in soup.html.body.findAll('input'):
      self.params[input['name']] = input['value']

    for select in soup.html.body.findAll(['select']):
      name = select['name']
      option = select.find('option', { "selected" : "SELECTED" })
      if option == None:
        self.params[name] = ''
      else:
        self.params[name] = option['value']

    for textarea in soup.html.body.find(['textarea']):
      self.params[textarea['name']] = '\n'.join(textarea.contents)


  def mark_out(self, message):
    self.mark(message, 0)

  def mark_in(self, message):
    self.mark(message, 1)

  def mark(self, message, presence):
    self.params['comment'] = message
    self.params['in_out'] = presence
    urllib.urlopen(self.url, urllib.urlencode(self.params))
