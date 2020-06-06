from xml.dom import minidom
xmldoc = minidom.parse('ancestorData3gens.xml')
itemlist = xmldoc.getElementsByTagName('Data')
print(len(itemlist))
print(itemlist[0])
for s in itemlist:
    print(s.childNodes[0].nodeValue)
