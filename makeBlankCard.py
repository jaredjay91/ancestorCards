from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from PIL import ImageOps
from tkinter import PhotoImage
import os
from myImages import *
from io import BytesIO
import base64


def makeBlankCard(gender = "male"):

    colorBlack = (0, 0, 0, 255)
    colorWhite = (255, 255, 255, 255)
    colorGold = (220, 200, 25, 255)
    colorRed = (255, 0, 0, 255)
    colorPink = (255, 182, 193, 255)
    colorGreen = (0, 255, 0, 255)
    colorBlue = (0, 0, 255, 255)
    colorLightBlue = (173,216,230, 255)
    colorYellow = (255, 255, 0, 255)
    colorGray = (155, 155, 155, 255)
    colorLightYellow = (255, 255, 170, 255)

    if gender=="female":
        parentshift = 50
        cardColor = colorPink
    elif gender=="male":
        parentshift = 0
        cardColor = colorLightBlue

    img = Image.new('RGBA', (600, 400), (0, 0, 0, 255))

    draw = ImageDraw.Draw(img)

    goldborder = Image.new('RGBA', (594, 394), colorGold)
    img.paste(goldborder, (2,2))

    blackline = Image.new('RGBA', (2, 400), colorBlack)
    img.paste(blackline, (299,2))

    whiterectangle = Image.new('RGBA', (286, 386), colorWhite)
    img.paste(whiterectangle, (6,6))

    #treepicfile = resource_path("treepic.png")
    #treepic = Image.open(treepicfile)
    treepic=treepic2String#GIF decoded to string. imageString from myimages.py
    #rendered = PhotoImage(data=treepic)
    rendered = Image.open(BytesIO(base64.b64decode(treepic)))
    img.paste(rendered, (6,6))

    blackrectangle = Image.new('RGBA', (286, 386), colorBlack)
    img.paste(blackrectangle, (306,6))

    leftpanelwidth = 56
    toppanelheight = 35
    personnumrec = Image.new('RGBA', (leftpanelwidth, toppanelheight), colorWhite)
    img.paste(personnumrec, (308,8))
    surnamenumrec = Image.new('RGBA', (leftpanelwidth, 380-toppanelheight), cardColor)
    img.paste(surnamenumrec, (308,10+toppanelheight))
    fullnamenumrec = Image.new('RGBA', (280-leftpanelwidth, toppanelheight), colorWhite)
    img.paste(fullnamenumrec, (310+leftpanelwidth,8))
    connectionsrec = Image.new('RGBA', (280-leftpanelwidth, 148), cardColor)
    img.paste(connectionsrec, (310+leftpanelwidth,242))
    birthrec = Image.new('RGBA', (280-leftpanelwidth, 50), cardColor)
    img.paste(birthrec, (310+leftpanelwidth,190))

    #relationship squares
    squarewidth = 30
    squareheight = 30
    blacksqr = Image.new('RGBA', (squarewidth+4, squareheight+4), colorBlack)
    whitesqr = Image.new('RGBA', (squarewidth, squareheight), colorWhite)
    blacksqr.paste(whitesqr, (2,2))
    personsqr = Image.new('RGBA', (squarewidth+4, squareheight+4), colorYellow)
    yellowsqr = Image.new('RGBA', (squarewidth, squareheight), colorLightYellow)
    personsqr.paste(whitesqr, (2,2))

    squarex = 425
    squarey = 300
    squaresep = 25
    horizline = Image.new('RGBA', (squaresep*2-squarewidth, 2), colorBlack)
    vertiline = Image.new('RGBA', (2, int(1.5*squaresep)), colorBlack)
    img.paste(horizline, (squarex-squaresep+squarewidth+parentshift+2,squarey-squaresep*2+int(squareheight/2)))#parents
    img.paste(horizline, (squarex+squarewidth+2,squarey+int(squareheight/2)))#couple
    img.paste(vertiline, (squarex+int(squarewidth/2)+parentshift,squarey-squaresep*2+int(squareheight/2)))#parents
    img.paste(vertiline, (squarex+squaresep+int(squarewidth/2),squarey+int(squareheight/2)))#couple
    img.paste(blacksqr, (squarex-squaresep+parentshift,squarey-squaresep*2))#father
    img.paste(blacksqr, (squarex+squaresep+parentshift,squarey-squaresep*2))#mother
    if gender=='male':
        img.paste(personsqr, (squarex,squarey))#man
        img.paste(blacksqr, (squarex+squaresep*2,squarey))#woman
    elif gender=='female':
        img.paste(blacksqr, (squarex,squarey))#man
        img.paste(personsqr, (squarex+squaresep*2,squarey))#woman
    img.paste(blacksqr, (squarex+squaresep,squarey+squaresep*2))#child

    #img.show()

    #Saved in the same relative location
    picname = "cards/blankCard" + gender + ".png"
    #print(picname)
    os.makedirs(os.path.dirname(picname), exist_ok=True)
    img.save(picname) 

def makeBlankInside():
    
    colorBlack = (0, 0, 0, 255)
    colorWhite = (255, 255, 255, 255)
    colorGold = (220, 200, 25, 255)

    img = Image.new('RGBA', (600, 400), (0, 0, 0, 255))

    draw = ImageDraw.Draw(img)
    
    goldborder = Image.new('RGBA', (594, 394), colorGold)
    img.paste(goldborder, (2,2))

    blackline = Image.new('RGBA', (2, 400), colorBlack)
    img.paste(blackline, (299,2))

    whiterectangle = Image.new('RGBA', (286, 386), colorWhite)
    img.paste(whiterectangle, (6,6))
    img.paste(whiterectangle, (306,6))


    #img.show()

    #Saved in the same relative location
    picname = "cards/blankInside.png"
    #print(picname)
    img.save(picname) 

#if __name__ == "__main__":
#    main()

