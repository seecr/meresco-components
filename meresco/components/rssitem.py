## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2007 SURFnet. http://www.surfnet.nl
#
#    This file is part of Meresco Components.
#
#    Meresco Components is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Components is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Components; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from meresco.components import XmlCompose
from xml.sax.saxutils import escape as xmlEscape
from urllib import quote as urlQuote

RSS_TEMPLATE = """<item>
    <title>%(title)s</title>
    <description>%(description)s</description>
    <link>%(link)s</link>
    <guid>%(link)s</guid>
</item>"""

class RssItem(XmlCompose):
    def __init__(self, nsMap, title, description, linkTemplate, **linkFields):
        XmlCompose.__init__(self,
            template="ignored",
            nsMap=nsMap,
            title=title,
            description=description,
            **linkFields)
        self._linkTemplate = linkTemplate
        assertLinkTemplate(linkTemplate, linkFields)

    def createRecord(self, dataDictionary):
        try:
            link = self._linkTemplate % dict(((k, urlQuote(v)) for k,v in dataDictionary.items()))
        except KeyError:
            link = ''
        rssData = {
            'link': xmlEscape(link),
            'description': xmlEscape(dataDictionary.get('description', '')),
            'title': xmlEscape(dataDictionary.get('title', ''))
        }
        return str(RSS_TEMPLATE % rssData)

def assertLinkTemplate(linkTemplate, linkFields):
    try:
        linkTemplate % dict(((k,'value') for k in linkFields.keys()))
    except KeyError, e:
        givenArguments = len(linkFields) + len(['self', 'nsMap', 'title', 'description', 'linkTemplate'])
        raise TypeError("__init__() takes at least %s arguments (%s given, missing %s)" % (givenArguments + 1, givenArguments, str(e)))
