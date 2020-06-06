
def main(file):

    filename = "XMLfile.xml"
    fh = open(filename, "w")

    startFileString = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
    XMLformatString = "<?mso-application progid=\"Excel.Sheet\"?><Workbook xmlns=\"urn:schemas-microsoft-com:office:spreadsheet\" xmlns:c=\"urn:schemas-microsoft-com:office:component:spreadsheet\" xmlns:html=\"http://www.w3.org/TR/REC-html40\" xmlns:o=\"urn:schemas-microsoft-com:office:office\" xmlns:ss=\"urn:schemas-microsoft-com:office:spreadsheet\" xmlns:x2=\"http://schemas.microsoft.com/office/excel/2003/xml\" xmlns:x=\"urn:schemas-microsoft-com:office:excel\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><OfficeDocumentSettings xmlns=\"urn:schemas-microsoft-com:office:office\"><Colors><Color><Index>3</Index><RGB>#c0c0c0</RGB></Color><Color><Index>4</Index><RGB>#ff0000</RGB></Color></Colors></OfficeDocumentSettings><ExcelWorkbook xmlns=\"urn:schemas-microsoft-com:office:excel\"><WindowHeight>9000</WindowHeight><WindowWidth>13860</WindowWidth><WindowTopX>240</WindowTopX><WindowTopY>75</WindowTopY><ProtectStructure>False</ProtectStructure><ProtectWindows>False</ProtectWindows></ExcelWorkbook><Styles><Style ss:ID=\"Default\" ss:Name=\"Default\"/><Style ss:ID=\"Result\" ss:Name=\"Result\"><Font ss:Bold=\"1\" ss:Italic=\"1\" ss:Underline=\"Single\"/></Style><Style ss:ID=\"Result2\" ss:Name=\"Result2\"><Font ss:Bold=\"1\" ss:Italic=\"1\" ss:Underline=\"Single\"/><NumberFormat ss:Format=\"Currency\"/></Style><Style ss:ID=\"Heading\" ss:Name=\"Heading\"><Font ss:Bold=\"1\" ss:Italic=\"1\" ss:Size=\"16\"/></Style><Style ss:ID=\"Heading1\" ss:Name=\"Heading1\"><Font ss:Bold=\"1\" ss:Italic=\"1\" ss:Size=\"16\"/></Style><Style ss:ID=\"co1\"/><Style ss:ID=\"ta1\"/></Styles><ss:Worksheet ss:Name=\"Sheet1\"><Table ss:StyleID=\"ta1\"><Column ss:Span=\"2\" ss:Width=\"64.01\"/>"
    startRowString = "<Row ss:Height=\"12.81\">"
    endRowString = "</Row>"
    startCellString = "<Cell><Data ss:Type=\"String\">"
    endCellString = "</Data></Cell>"
    endFileString = "</Table><x:WorksheetOptions/></ss:Worksheet></Workbook>"

    fh.write(startFileString)
    fh.write(XMLformatString)

    text_file = file
    while True:
        #read info from csv file #personnum;fullname;surname;gender;birthdate;birthplace;deathdate;deathplace;fathernum;mothernum;spousenum;childnum;Life Summary
        persondata = ['','','','','','','','','','','','','']
        personstring = text_file.readline()
        if not personstring:
            break
        arraylength = len(persondata)
        numchars = len(personstring)
        start = 0
        end = 0
        index = 0
        #print(personstring)
        while end<numchars:
            strend = personstring[end]
            if index<arraylength-1:
                while strend != ';':
                    end = end + 1
                    strend = personstring[end]
            else:
                end = numchars
            persondata[index] = personstring[start:end]
            #print(persondata[index])
            index = index + 1
            start = end + 1
            end = start

        #write to XML file
        fh.write(startRowString)
        for i in range(0,arraylength):
            fh.write(startCellString+persondata[i]+endCellString)
        fh.write(endRowString)

    fh.write(endFileString)
    fh.close()

if __name__ == "__main__":
    csvFile = open("ancestorData.csv", "r")
    main(csvFile)
    csvFile.close()
