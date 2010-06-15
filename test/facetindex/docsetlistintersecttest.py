## begin license ##
#
#    Meresco Components are components to build searchengines, repositories
#    and archives, based on Meresco Core.
#    Copyright (C) 2010 Seek You Too (CQ2) http://www.cq2.nl
#    Copyright (C) 2010 Stichting Kennisnet http://www.kennisnet.nl
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
from unittest import TestCase
from meresco.components.facetindex import DocSet, DocSetList, __file__ as facetindexinitfile

class DocSetListIntersectTest(TestCase):
    def testTermIntersect(self):
        adsl = createEdurepDocsetList()

        dsl0 = createEdurepDocsetList()
        dsl1 = createSmoDocsetList()
        termIntersect = dsl1.termIntersect(dsl0)
        # this termIntersect used to fail.
        #  It succeeded after changing the generic intersect with the following changes
        #
        #--- ../../meresco/components/facetindex/docset.h.wrong	2010-05-28 12:42:05.000000000 +0200
        #+++ ../../meresco/components/facetindex/docset.h	2010-05-28 12:35:56.000000000 +0200
        #@@ -148,12 +148,10 @@
        #             ForwardIterator lhs = lhs_from; // Reassign slow iterator to faster one (pointer)
        #             ForwardIterator rhs = rhs_from;
        #             while ( 1 ) {
        #-                while (*rhs++ < *lhs); // terminates without boundary checks
        #-                rhs--;
        #+                while ( rhs < rhs_till && *rhs < *lhs ) rhs++;
        #                 if ( rhs >= rhs_till )
        #                     return;
        #-                while (*lhs++ < *rhs); // terminates without boundary checks
        #-                lhs--;
        #+                while ( lhs < lhs_till && *lhs < *rhs ) lhs++;
        #                 if ( lhs >= lhs_till )
        #                     return;
        #                 if ( *lhs == *rhs ) {


def createSmoDocsetList():
    dsl1 = DocSetList()
    dsl1.add(DocSet([67L, 68L, 69L, 70L, 71L, 73L, 84L]), "boomroosvis.txt")
    dsl1.add(DocSet([74L, 75L, 76L, 77L, 78L, 85L]), "ftp://boomroosvis.com")
    dsl1.add(DocSet([58L]), "http://a9.com")
    dsl1.add(DocSet([41L, 43L, 45L, 47L, 49L, 52L, 54L]), "http://google.com")
    dsl1.add(DocSet([66L, 79L]), "http://www.12345678.eu")
    dsl1.add(DocSet([80L, 82L, 83L]), "http://www.boomroosvis.nl")
    dsl1.add(DocSet([24L]), "http://www.eur.nl/")
    dsl1.add(DocSet([21L]), "http://www.fauxpress.com/kimball/ex/po.htm")
    dsl1.add(DocSet([3L]), "http://www.ficusforever.nl")
    dsl1.add(DocSet([16L]), "http://www.filmfocus.nl/films/26917-Funny-Games-US.html")
    dsl1.add(DocSet([5L]), "http://www.freshdelmonte.com%C3%BCmlat.html&q=name")
    dsl1.add(DocSet([42L, 44L, 46L, 48L, 50L, 53L, 55L]), "http://www.live.com/")
    dsl1.add(DocSet([23L]), "http://www.nu.nl")
    dsl1.add(DocSet([8L]), "http://www.onderwijsrepository.nl/fedora/get/id:128/DS1/2007-05-23T08:14:27.920Z")
    dsl1.add(DocSet([28L]), "http://www.putty.org")
    dsl1.add(DocSet([86L, 87L, 88L]), "http://www.sabje.com")
    dsl1.add(DocSet([1L, 2L, 4L]), "http://www.samenmaken.nl:8080/fedora/get/smpid:100/DS2")
    dsl1.add(DocSet([39L]), "http://www.taptoe.nl/datacon/spreekbeurt_old.asp?ItemId=15")
    dsl1.add(DocSet([0L, 6L, 7L, 10L, 11L, 12L, 13L, 14L, 15L, 22L, 25L, 26L, 30L, 31L, 32L, 35L, 36L, 56L, 59L, 61L, 63L, 64L]), "http://www.teachers.tv/")
    dsl1.add(DocSet([27L]), "http://www.teachers.tv/update")
    dsl1.add(DocSet([60L]), "http://www.wrecker.nl")
    dsl1.add(DocSet([57L]), "http://yahoo.com")
    dsl1.add(DocSet([37L]), "test")
    dsl1.add(DocSet([38L]), "tralala")
    dsl1.add(DocSet([18L]), "www.iphoneclub.nl")
    dsl1.add(DocSet([17L, 20L]), "www.nu.nl")
    dsl1.add(DocSet([33L]), "xfgmj")
    dsl1.add(DocSet([34L]), "zcj")
    return dsl1

def createEdurepDocsetList():
    dsl0 = DocSetList()
    dsl0.add(DocSet([118L]), "163645")
    dsl0.add(DocSet([88L]), "193514")
    dsl0.add(DocSet([87L]), "193518")
    dsl0.add(DocSet([86L]), "193520")
    dsl0.add(DocSet([85L]), "193521")
    dsl0.add(DocSet([84L]), "193533")
    dsl0.add(DocSet([83L]), "193535")
    dsl0.add(DocSet([82L]), "193536")
    dsl0.add(DocSet([91L]), "193654")
    dsl0.add(DocSet([90L]), "193656")
    dsl0.add(DocSet([89L]), "193659")
    dsl0.add(DocSet([90L]), "978-90-01-70297-7")
    dsl0.add(DocSet([91L]), "978-90-01-70299-1")
    dsl0.add(DocSet([89L]), "978-90-01-71826-8")
    dsl0.add(DocSet([88L]), "978-90-460-0512-5")
    dsl0.add(DocSet([87L]), "978-90-460-0515-6")
    dsl0.add(DocSet([86L]), "978-90-460-0516-3")
    dsl0.add(DocSet([85L]), "978-90-460-0517-0")
    dsl0.add(DocSet([84L]), "978-90-460-0543-9")
    dsl0.add(DocSet([83L]), "978-90-460-0545-3")
    dsl0.add(DocSet([82L]), "978-90-460-0546-0")
    dsl0.add(DocSet([71L]), "http://na.memorix.nl/oai2/?image=na:col1:dat520922:345669.jpg&type=large")
    dsl0.add(DocSet([43L]), "http://natschool.rocleiden.nl/Services/CMS.asmx/ExportPackage?packageId=2198223&exportType=Automatic")
    dsl0.add(DocSet([38L]), "http://natschool.rocleiden.nl/Services/CMS.asmx/ExportPackage?packageId=2198225&exportType=Automatic")
    dsl0.add(DocSet([44L]), "http://natschool.rocleiden.nl/Services/CMS.asmx/ExportPackage?packageId=2198230&exportType=Automatic")
    dsl0.add(DocSet([42L]), "http://natschool.rocleiden.nl/Services/CMS.asmx/ExportPackage?packageId=2198236&exportType=Automatic")
    dsl0.add(DocSet([39L]), "http://natschool.rocleiden.nl/Services/CMS.asmx/ExportPackage?packageId=2198237&exportType=Automatic")
    dsl0.add(DocSet([46L]), "http://natschool.rocleiden.nl/Services/CMS.asmx/ExportPackage?packageId=2198242&exportType=Automatic")
    dsl0.add(DocSet([47L]), "http://natschool.rocleiden.nl/Services/CMS.asmx/ExportPackage?packageId=2198243&exportType=Automatic")
    dsl0.add(DocSet([45L]), "http://natschool.rocleiden.nl/Services/CMS.asmx/ExportPackage?packageId=2285347&exportType=Automatic")
    dsl0.add(DocSet([40L]), "http://natschool.rocleiden.nl/Services/CMS.asmx/ExportPackage?packageId=2446368&exportType=Automatic")
    dsl0.add(DocSet([9L]), "http://nl.wikipedia.org/wiki/Aardbeving_Indische_Oceaan_2004")
    dsl0.add(DocSet([108L]), "http://ovc.lesbank.nl/74D9")
    dsl0.add(DocSet([109L]), "http://ovc.lesbank.nl/79E8")
    dsl0.add(DocSet([115L]), "http://ovc.lesbank.nl/79F1")
    dsl0.add(DocSet([114L]), "http://ovc.lesbank.nl/79F3")
    dsl0.add(DocSet([113L]), "http://ovc.lesbank.nl/79F6")
    dsl0.add(DocSet([112L]), "http://ovc.lesbank.nl/79FA")
    dsl0.add(DocSet([111L]), "http://ovc.lesbank.nl/79FD")
    dsl0.add(DocSet([110L]), "http://ovc.lesbank.nl/79FE")
    dsl0.add(DocSet([117L]), "http://ovc.lesbank.nl/7A37")
    dsl0.add(DocSet([116L]), "http://ovc.lesbank.nl/7AA8")
    dsl0.add(DocSet([20L]), "http://proto4.thinkquest.nl/%7Elld669")
    dsl0.add(DocSet([95L]), "http://provisioning.ontwikkelcentrum.nl/Default.aspx?id=OC-031028-8.wmv&format=wmv&mode=single")
    dsl0.add(DocSet([93L]), "http://provisioning.ontwikkelcentrum.nl/Default.aspx?id=OC-10000")
    dsl0.add(DocSet([94L]), "http://provisioning.ontwikkelcentrum.nl/Default.aspx?id=OC-10000-a")
    dsl0.add(DocSet([92L]), "http://provisioning.ontwikkelcentrum.nl/Default.aspx?id=OC-10000p1-1")
    dsl0.add(DocSet([101L]), "http://provisioning.ontwikkelcentrum.nl/Default.aspx?id=OC-10000p5-3")
    dsl0.add(DocSet([99L]), "http://provisioning.ontwikkelcentrum.nl/Default.aspx?id=OC-10001")
    dsl0.add(DocSet([100L]), "http://provisioning.ontwikkelcentrum.nl/Default.aspx?id=OC-10001-a")
    dsl0.add(DocSet([98L]), "http://provisioning.ontwikkelcentrum.nl/Default.aspx?id=OC-10001p1-1")
    dsl0.add(DocSet([97L]), "http://provisioning.ontwikkelcentrum.nl/Default.aspx?id=OC-10001p1-2")
    dsl0.add(DocSet([96L]), "http://provisioning.ontwikkelcentrum.nl/Default.aspx?id=OC-10001p1-3")
    dsl0.add(DocSet([0L]), "http://take-shape-share.fenc.org.uk/rsrc/rsrc_opn.aspx?id=1002")
    dsl0.add(DocSet([1L]), "http://take-shape-share.fenc.org.uk/rsrc/rsrc_opn.aspx?id=1012")
    dsl0.add(DocSet([3L]), "http://take-shape-share.fenc.org.uk/rsrc/rsrc_opn.aspx?id=1022")
    dsl0.add(DocSet([4L]), "http://take-shape-share.fenc.org.uk/rsrc/rsrc_opn.aspx?id=222")
    dsl0.add(DocSet([5L]), "http://take-shape-share.fenc.org.uk/rsrc/rsrc_opn.aspx?id=2232")
    dsl0.add(DocSet([6L]), "http://take-shape-share.fenc.org.uk/rsrc/rsrc_opn.aspx?id=2242")
    dsl0.add(DocSet([7L]), "http://take-shape-share.fenc.org.uk/rsrc/rsrc_opn.aspx?id=2252")
    dsl0.add(DocSet([8L]), "http://take-shape-share.fenc.org.uk/rsrc/rsrc_opn.aspx?id=2262")
    dsl0.add(DocSet([27L]), "http://videotheek.surfnet.nl/play_proxy/mmc/21783/ADC_10.wmv")
    dsl0.add(DocSet([104L]), "http://webpad-afval.yurls.net")
    dsl0.add(DocSet([102L]), "http://webpad-bedreigde-dieren.yurls.net")
    dsl0.add(DocSet([103L]), "http://webpad-middeleeuwen.yurls.net")
    dsl0.add(DocSet([26L]), "http://www.abc-of-fitness.com/start-fitness-program/components-of-fitness.asp")
    dsl0.add(DocSet([10L]), "http://www.artis.nl/webuil/e_aardbevingen_01.html")
    dsl0.add(DocSet([24L]), "http://www.dansserver.nl/")
    dsl0.add(DocSet([28L]), "http://www.ecologiebibliotheek.nl/spitten.htm")
    dsl0.add(DocSet([29L]), "http://www.egelopvang.nl/egelleven.htm#Waarschuwingen")
    dsl0.add(DocSet([30L]), "http://www.ei-info.nl")
    dsl0.add(DocSet([31L]), "http://www.energy-online.nl")
    dsl0.add(DocSet([32L]), "http://www.eucalypta.nl")
    dsl0.add(DocSet([33L]), "http://www.famlodder.nl/caviainfo.htm")
    dsl0.add(DocSet([18L]), "http://www.fauxpress.com/kimball/ex/po.htm")
    dsl0.add(DocSet([34L]), "http://www.fcdf.nl")
    dsl0.add(DocSet([35L]), "http://www.ficusforever.nl")
    dsl0.add(DocSet([36L]), "http://www.flowercouncil.org/nl/plantscope/default.asp")
    dsl0.add(DocSet([37L]), "http://www.freshdelmonte.com")
    dsl0.add(DocSet([25L]), "http://www.huidinfo.nl/botoxrimpels.html")
    dsl0.add(DocSet([19L]), "http://www.kinderenwebhotel.be/WO_tijd/vervoer.htm")
    dsl0.add(DocSet([12L]), "http://www.knmi.nl/VinkCMS/dossier_detail.jsp?id=15339")
    dsl0.add(DocSet([118L]), "http://www.leermiddelenplein.nl/php/detail.php?id=163645")
    dsl0.add(DocSet([88L]), "http://www.leermiddelenplein.nl/php/detail.php?id=193514")
    dsl0.add(DocSet([87L]), "http://www.leermiddelenplein.nl/php/detail.php?id=193518")
    dsl0.add(DocSet([86L]), "http://www.leermiddelenplein.nl/php/detail.php?id=193520")
    dsl0.add(DocSet([85L]), "http://www.leermiddelenplein.nl/php/detail.php?id=193521")
    dsl0.add(DocSet([84L]), "http://www.leermiddelenplein.nl/php/detail.php?id=193533")
    dsl0.add(DocSet([83L]), "http://www.leermiddelenplein.nl/php/detail.php?id=193535")
    dsl0.add(DocSet([82L]), "http://www.leermiddelenplein.nl/php/detail.php?id=193536")
    dsl0.add(DocSet([91L]), "http://www.leermiddelenplein.nl/php/detail.php?id=193654")
    dsl0.add(DocSet([90L]), "http://www.leermiddelenplein.nl/php/detail.php?id=193656")
    dsl0.add(DocSet([89L]), "http://www.leermiddelenplein.nl/php/detail.php?id=193659")
    dsl0.add(DocSet([90L]), "http://www.leermiddelenplein.nl/php/detail.php?id=978-90-01-70297-7")
    dsl0.add(DocSet([91L]), "http://www.leermiddelenplein.nl/php/detail.php?id=978-90-01-70299-1")
    dsl0.add(DocSet([89L]), "http://www.leermiddelenplein.nl/php/detail.php?id=978-90-01-71826-8")
    dsl0.add(DocSet([88L]), "http://www.leermiddelenplein.nl/php/detail.php?id=978-90-460-0512-5")
    dsl0.add(DocSet([87L]), "http://www.leermiddelenplein.nl/php/detail.php?id=978-90-460-0515-6")
    dsl0.add(DocSet([86L]), "http://www.leermiddelenplein.nl/php/detail.php?id=978-90-460-0516-3")
    dsl0.add(DocSet([85L]), "http://www.leermiddelenplein.nl/php/detail.php?id=978-90-460-0517-0")
    dsl0.add(DocSet([84L]), "http://www.leermiddelenplein.nl/php/detail.php?id=978-90-460-0543-9")
    dsl0.add(DocSet([83L]), "http://www.leermiddelenplein.nl/php/detail.php?id=978-90-460-0545-3")
    dsl0.add(DocSet([82L]), "http://www.leermiddelenplein.nl/php/detail.php?id=978-90-460-0546-0")
    dsl0.add(DocSet([22L]), "http://www.medicinfo.nl/{b29eb02a-2fc6-4dd1-8487-5f645c7081fa}")
    dsl0.add(DocSet([74L]), "http://www.museumkennis.nl/lp.rmv/museumkennis/i000101.html")
    dsl0.add(DocSet([73L]), "http://www.museumkennis.nl/lp.rmv/museumkennis/i000102.html")
    dsl0.add(DocSet([80L]), "http://www.museumkennis.nl/lp.rmv/museumkennis/i000103.html")
    dsl0.add(DocSet([79L]), "http://www.museumkennis.nl/lp.rmv/museumkennis/i000104.html")
    dsl0.add(DocSet([78L]), "http://www.museumkennis.nl/lp.rmv/museumkennis/i000105.html")
    dsl0.add(DocSet([77L]), "http://www.museumkennis.nl/lp.rmv/museumkennis/i000106.html")
    dsl0.add(DocSet([76L]), "http://www.museumkennis.nl/lp.rmv/museumkennis/i000107.html")
    dsl0.add(DocSet([75L]), "http://www.museumkennis.nl/lp.rmv/museumkennis/i000108.html")
    dsl0.add(DocSet([81L]), "http://www.museumkennis.nl/lp.rmv/museumkennis/i000118.html")
    dsl0.add(DocSet([14L]), "http://www.natuurinformatie.nl/ndb.mcp/natuurdatabase.nl/i000332.html")
    dsl0.add(DocSet([13L]), "http://www.nos.nl/jeugdjournaal/uitleg/Londen_aanslagen/Londen_aanslagen.html")
    dsl0.add(DocSet([48L]), "http://www.onderwijsrepository.nl/fedora/get/id:122/DS1/2007-05-10T08:48:42.462Z")
    dsl0.add(DocSet([49L]), "http://www.onderwijsrepository.nl/fedora/get/id:128/DS1/2007-05-23T08:14:27.920Z")
    dsl0.add(DocSet([50L]), "http://www.onderwijsrepository.nl/fedora/get/id:129/DS1/2007-05-23T08:12:40.465Z")
    dsl0.add(DocSet([51L]), "http://www.onderwijsrepository.nl/fedora/get/id:130/DS1/2007-05-23T08:20:42.040Z")
    dsl0.add(DocSet([52L]), "http://www.onderwijsrepository.nl/fedora/get/id:131/DS1/2007-05-23T08:25:01.670Z")
    dsl0.add(DocSet([53L]), "http://www.onderwijsrepository.nl/fedora/get/id:132/DS1/2007-05-23T08:29:50.674Z")
    dsl0.add(DocSet([54L]), "http://www.onderwijsrepository.nl/fedora/get/id:133/DS1/2007-05-23T08:33:14.342Z")
    dsl0.add(DocSet([55L]), "http://www.onderwijsrepository.nl/fedora/get/id:134/DS1/2007-05-23T09:00:33.303Z")
    dsl0.add(DocSet([56L]), "http://www.onderwijsrepository.nl/fedora/get/id:135/DS1/2007-05-23T11:42:13.393Z")
    dsl0.add(DocSet([57L]), "http://www.onderwijsrepository.nl/fedora/get/id:136/DS1/2007-05-23T12:01:22.670Z")
    dsl0.add(DocSet([58L]), "http://www.onderwijsrepository.nl/fedora/get/id:137/DS1/2007-05-23T12:11:43.783Z")
    dsl0.add(DocSet([59L]), "http://www.onderwijsrepository.nl/fedora/get/id:221/DS1/2007-06-08T09:21:19.598Z")
    dsl0.add(DocSet([60L]), "http://www.onderwijsrepository.nl/fedora/get/id:229/DS1/2007-06-08T09:28:25.950Z")
    dsl0.add(DocSet([107L]), "http://www.ontwikkelcentrum.nl/kennisnet/data/digitop/OCHB-00001/OCHB-00001.doc")
    dsl0.add(DocSet([106L]), "http://www.ontwikkelcentrum.nl/kennisnet/data/digitop/OCHB-00002/OCHB-00002.wmv")
    dsl0.add(DocSet([105L]), "http://www.ontwikkelcentrum.nl/kennisnet/data/digitop/OCHB-00003/OCHB-00003.html")
    dsl0.add(DocSet([23L]), "http://www.psychowijzer.nl/pagina/stress--overspannenheid-en-burn-out.p25.html")
    dsl0.add(DocSet([17L]), "http://www.roczeeland.nl")
    dsl0.add(DocSet([61L]), "http://www.samenmaken.nl:8080/fedora/get/smpid:10/europeanen_ontdekken_de_wereld.flp")
    dsl0.add(DocSet([62L]), "http://www.samenmaken.nl:8080/fedora/get/smpid:100/DS2")
    dsl0.add(DocSet([63L]), "http://www.samenmaken.nl:8080/fedora/get/smpid:102/DS3")
    dsl0.add(DocSet([64L]), "http://www.samenmaken.nl:8080/fedora/get/smpid:103/DS3")
    dsl0.add(DocSet([65L]), "http://www.samenmaken.nl:8080/fedora/get/smpid:104/DS1")
    dsl0.add(DocSet([66L]), "http://www.samenmaken.nl:8080/fedora/get/smpid:105/DS2")
    dsl0.add(DocSet([67L]), "http://www.samenmaken.nl:8080/fedora/get/smpid:106/DS1")
    dsl0.add(DocSet([68L]), "http://www.samenmaken.nl:8080/fedora/get/smpid:107/DS2")
    dsl0.add(DocSet([69L]), "http://www.samenmaken.nl:8080/fedora/get/smpid:108/DS1")
    dsl0.add(DocSet([70L]), "http://www.samenmaken.nl:8080/fedora/get/smpid:109/DS1")
    dsl0.add(DocSet([72L]), "http://www.samenmaken.nl:8080/get/smpid:2671/DS1")
    dsl0.add(DocSet([16L]), "http://www.samsam.kennisnet.nl/archief/Afghanistan/")
    dsl0.add(DocSet([15L]), "http://www.samsam.kennisnet.nl/archief/aids/#")
    dsl0.add(DocSet([21L]), "http://www.sportunterricht.de/animation/stabani2.html")
    dsl0.add(DocSet([11L]), "http://www.taptoe.nl/datacon/spreekbeurt_old.asp?ItemId=15")
    dsl0.add(DocSet([71L]), "memorix::col1:dat520922")
    dsl0.add(DocSet([28L]), "oai:library.wur.nl:gkn/1800309")
    dsl0.add(DocSet([29L]), "oai:library.wur.nl:gkn/1800315")
    dsl0.add(DocSet([30L]), "oai:library.wur.nl:gkn/1800316")
    dsl0.add(DocSet([31L]), "oai:library.wur.nl:gkn/1800322")
    dsl0.add(DocSet([32L]), "oai:library.wur.nl:gkn/1800328")
    dsl0.add(DocSet([33L]), "oai:library.wur.nl:gkn/1800334")
    dsl0.add(DocSet([34L]), "oai:library.wur.nl:gkn/1800340")
    dsl0.add(DocSet([35L]), "oai:library.wur.nl:gkn/1800347")
    dsl0.add(DocSet([36L]), "oai:library.wur.nl:gkn/1800353")
    dsl0.add(DocSet([37L]), "oai:library.wur.nl:gkn/1800359")
    dsl0.add(DocSet([95L]), "oai:www.ontwikkelcentrum.nl:gkn/OC-031028-8")
    dsl0.add(DocSet([93L]), "oai:www.ontwikkelcentrum.nl:gkn/OC-10000")
    dsl0.add(DocSet([94L]), "oai:www.ontwikkelcentrum.nl:gkn/OC-10000-a")
    dsl0.add(DocSet([92L]), "oai:www.ontwikkelcentrum.nl:gkn/OC-10000p1-1")
    dsl0.add(DocSet([101L]), "oai:www.ontwikkelcentrum.nl:gkn/OC-10000p5-3")
    dsl0.add(DocSet([99L]), "oai:www.ontwikkelcentrum.nl:gkn/OC-10001")
    dsl0.add(DocSet([100L]), "oai:www.ontwikkelcentrum.nl:gkn/OC-10001-a")
    dsl0.add(DocSet([98L]), "oai:www.ontwikkelcentrum.nl:gkn/OC-10001p1-1")
    dsl0.add(DocSet([97L]), "oai:www.ontwikkelcentrum.nl:gkn/OC-10001p1-2")
    dsl0.add(DocSet([96L]), "oai:www.ontwikkelcentrum.nl:gkn/OC-10001p1-3")
    dsl0.add(DocSet([107L]), "oai:www.ontwikkelcentrum.nl:gkn/OCHB-00001")
    dsl0.add(DocSet([106L]), "oai:www.ontwikkelcentrum.nl:gkn/OCHB-00002")
    dsl0.add(DocSet([105L]), "oai:www.ontwikkelcentrum.nl:gkn/OCHB-00003")
    dsl0.add(DocSet([104L]), "oai:www.ontwikkelcentrum.nl:gkn/OCHB-00004")
    dsl0.add(DocSet([103L]), "oai:www.ontwikkelcentrum.nl:gkn/OCHB-00005")
    dsl0.add(DocSet([102L]), "oai:www.ontwikkelcentrum.nl:gkn/OCHB-00006")
    return dsl0