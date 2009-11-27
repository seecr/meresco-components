from merescocore.framework import Observable

from storage.storage import unescapeName
from xml.sax.saxutils import escape as xml_escape
from os.path import basename
from StringIO import StringIO
from lxml.etree import parse, tostring

EXTENSION = '.record'

class XmlDocumentAdapter(Observable):
    """
    This class wraps a single lxmlNode into a document as expected by many of
    the Meresco components.  It splits the identifier into a repository and a
    record identifier by splitting on the first collon. Also, it only responds
    to identifiers ending with '.record'. As an example:

        <repository id>:<record id>.record.

    will be wrapped in a <document> tag, with a <header> and a <meta> containing
    the repository and record id extracted from the input identifier.  The
    original record is put in the <metadata> tag.
    """

    def _splitFilename(self, aString):
        if aString.endswith(EXTENSION):
            parts = aString[:-len(EXTENSION)].split(':', 1)
            if len(parts) == 2:
                repository, identifier = parts
                return repository, unescapeName(identifier)
        return ('', '')

    def _createRecord(self, repository, identifier, lxmlNode):
        header = xml_escape("""<header xmlns="http://www.openarchives.org/OAI/2.0/">
            <identifier>%(identifier)s</identifier>
        </header>""" % locals())

        meta = xml_escape("""<meta xmlns="http://meresco.com/namespace/harvester/meta">
  <upload><id>%(repository)s:%(identifier)s</id></upload>
  <record>
    <id>%(identifier)s</id>
  </record>
  <repository>
    <id>%(repository)s</id>
  </repository>
</meta>""" % locals())
        metadata = xml_escape("""<metadata xmlns="http://www.openarchives.org/OAI/2.0/">%s</metadata>""" % tostring(lxmlNode))

        return parse(StringIO("""<document xmlns="http://meresco.com/namespace/harvester/document"><part name="header">%(header)s</part><part name="meta">%(meta)s</part><part name="metadata">%(metadata)s</part></document>""" % locals()))

    def add(self, identifier=None, lxmlNode=None):
        repositoryId, recordId = self._splitFilename(identifier)
        if repositoryId == '' or recordId == '':
            return

        self.do.add(identifier=recordId, lxmlNode=self._createRecord(repositoryId, recordId, lxmlNode))