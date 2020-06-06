from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from PIL import ImageOps
import easygui
import math

def convertDate(date='00000101'):

    if len(date)==8:
        year = date[0:4]
        month = date[4:6]
        day = date[6:8]
        print(year)
        print(month)
        print(day)
        if month=='01':
            month = 'Jan'
        elif month=='02':
            month = 'Feb'
        elif month=='03':
            month = 'Mar'
        elif month=='04':
            month = 'Apr'
        elif month=='05':
            month = 'May'
        elif month=='06':
            month = 'Jun'
        elif month=='07':
            month = 'Jul'
        elif month=='08':
            month = 'Aug'
        elif month=='09':
            month = 'Sep'
        elif month=='10':
            month = 'Oct'
        elif month=='11':
            month = 'Nov'
        elif month=='12':
            month = 'Dec'
        date = day + ' ' + month + ' ' + year
    return date

def main():

    #Define text fonts
    textboxwidth = 300-12
    storyfontsize = 24
    strwidth = int(textboxwidth/storyfontsize*2)
    storyfont = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSans.ttf", storyfontsize, encoding="unic")
    fullnamefont = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSans.ttf", 16, encoding="unic")
    surnamefont = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSans.ttf", 36, encoding="unic")
    birthfont = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSans.ttf", 16, encoding="unic")
    numfont = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSans.ttf", 9, encoding="unic")
    longfullnamefont = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSans.ttf", 12, encoding="unic")
    longsurnamefont = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSans.ttf", 30, encoding="unic")

    #Define colors
    colorstrings = ["Blue","Green","Red","Yellow","Gray"]
    colorBlack = (0, 0, 0, 255)
    colorWhite = (255, 255, 255, 255)
    colorGold = (220, 200, 25, 255)
    colorRed = (255, 0, 0, 255)
    colorGreen = (0, 255, 0, 255)
    colorBlue = (0, 0, 255, 255)
    colorYellow = (255, 255, 0, 255)
    colorGray = (155, 155, 155, 255)
    colorPink = (255, 182, 193, 255)
    colorLightBlue = (173,216,230, 255)
    nocolor = (0,0,0,0)

    #Initialize parameters
    gender = "male"
    cardColor = "Gray"

    #open text file
    text_file = open("ancestorDataFSstyle.csv", "r")
    personstring = text_file.readline()

    for i in range(0,5):
        #read info from file
        #personnum;fullname;surname;gender;birthdate;birthplace;deathdate;deathplace;fathernum;mothernum;spousenum;childnum;Life Summary
        persondata = ['','','','','','','','','','','','','']
        personstring = text_file.readline()
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
            print(persondata[index])
            index = index + 1
            start = end + 1
            end = start

        personnum = persondata[0]
        fullname = persondata[1] + ' ' + persondata[2]
        surname = persondata[2].upper()
        birth = persondata[4]
        death = persondata[6]
        fathernum = persondata[8]
        mothernum = persondata[9]
        spousenum = persondata[10]
        childnum = persondata[11]
        story = persondata[12]

        birth = convertDate(birth)
        death = convertDate(death)

        #Load blank card
        if persondata[3]=='M':
            gender = 'male'
            personx = 428
            spousex = 478
            cardColor = colorLightBlue
        elif persondata[3]=='F':
            gender = 'female'
            personx = 478
            spousex = 428
            cardColor = colorPink
        filename = "cards/blankCard" + gender + ".png"
        img = Image.open(filename)
        draw = ImageDraw.Draw(img)

        #write on card
        # draw.text((x, y),"Sample Text",(r,g,b))

        #person id number
        draw.text((310, 8),personnum[0:4]+'\n '+personnum[4:8],(0,0,0),font=fullnamefont)

        #full name
        if len(fullname)<25:
            draw.text((370, 12),fullname,(0,0,0),font=fullnamefont)
        else:
            draw.text((370, 12),fullname,(0,0,0),font=longfullnamefont)

        #birth and death
        draw.text((370, 200),'b. ' + birth,(0,0,0),font=birthfont)
        draw.text((370, 220),'d. ' + death,(0,0,0),font=birthfont)

        #relationships
        parentsy = 255
        draw.text((personx-25, parentsy),fathernum[0:4]+'\n '+fathernum[4:8],(0,0,0),font=numfont)
        draw.text((personx+25, parentsy),mothernum[0:4]+'\n '+mothernum[4:8],(0,0,0),font=numfont)
        draw.text((personx, parentsy+50),personnum[0:4]+'\n '+personnum[4:8],(0,0,0),font=numfont)
        draw.text((spousex, parentsy+50),spousenum[0:4]+'\n '+spousenum[4:8],(0,0,0),font=numfont)
        draw.text((454, parentsy+100),childnum[0:4]+'\n '+childnum[4:8],(0,0,0),font=numfont)

        #make big rotated surname
        leftpanelwidth = 56
        toppanelheight = 35
        surnametxt = Image.new('RGBA', (380-toppanelheight, leftpanelwidth), cardColor)
        surnamepic = ImageDraw.Draw(surnametxt)
        if len(surname)<12:
            surnamepic.text((0, 0),surname,(0,0,0),font=surnamefont)
        else:
            surnamepic.text((0, 0),surname,(0,0,0),font=longsurnamefont)
        #widthnorot, heightnorot = surnametxt.size
        #print('width = ',widthnorot)
        #print('height = ',heightnorot)
        surnamerot = surnametxt.rotate(90, expand=1)
        widthrot, heightrot = surnamerot.size
        #print('width = ',widthrot)
        #print('height = ',heightrot)
        surnamecrop = surnamerot.crop((1, 0, widthrot, heightrot-1))
        #widthrot, heightrot = surnamecrop.size
        #print('width = ',widthrot)
        #print('height = ',heightrot)
        img.paste(surnamecrop, (307,9+toppanelheight))

        #paste photo
        #photoname = "Photos/pic" + personnum + ".png"
        photoname = "Photos/pic" + personnum + ".png"
        try:
            photo = Image.open(photoname)
        except FileNotFoundError:
            print('please select photo file for ',fullname)
            photoname = easygui.fileopenbox()
        photo = Image.open(photoname)
        photo.save('Photos/pic' + personnum + '.png')
        width, height = photo.size
        newheight = 178-toppanelheight
        hratio = newheight/height
        newwidth = int((width*float(hratio)))
        photo = photo.resize((newwidth,newheight), Image.ANTIALIAS)
        width, height = photo.size
        if width > 280-leftpanelwidth:
            newwidth = 280-leftpanelwidth
            wratio = newwidth/width
            newheight = int((height*float(wratio)))
            photo = photo.resize((newwidth,newheight), Image.ANTIALIAS)
        xcenter = (280-leftpanelwidth)/2 + leftpanelwidth + 310
        ycenter = (178-toppanelheight)/2 + toppanelheight + 10
        xpic = int(xcenter - width/2)
        ypic = int(ycenter - height/2)
        img.paste(photo,(xpic,ypic))

        #img.show()

        #Saved in the same relative location
        picname = "cards/card" + personnum + ".png"
        print(picname)
        img.save(picname) 

        #STORY INSIDE
        storylength = len(story)
        numlines = int(storylength/strwidth)

        #Load blank card
        imginside = Image.open("cards/blankInside.png")
        draw = ImageDraw.Draw(imginside)

        #write on card line by line
        start = 0
        end = strwidth
        xshift = 0
        yshift = 0
        j = 0
        while end<storylength:
            xpos = 12 + xshift
            ypos = 12 + j*storyfontsize + yshift
            strend = story[end]
            while strend!=" ":
                end = end-1
                strend = story[end]
            end = end+1
            strpart = story[start:end]
            print("strpart = ",strpart)

            if ypos>360:
                yshift = 12-ypos
                ypos = ypos+yshift
                xshift = 300
                xpos = xpos+300
            draw.text((xpos, ypos),strpart,(0,0,0),font=storyfont)

            start = end
            end = end+strwidth
            j = j+1

        end = storylength
        strpart = story[start:end]
        print("strpart = ",strpart)
        ypos = ypos+storyfontsize
        print("ypos = ",ypos)
        if ypos>360:
            yshift = 12-ypos
            ypos = ypos+yshift
            xshift = 300
            xpos = xpos+300
        draw.text((xpos, ypos),strpart,(0,0,0),font=storyfont)


        #imginside.show()

        #Saved in the same relative location
        picinsidename = "cardsFSstyle/card" + personnum + "inside.png"
        print(picinsidename)
        imginside.save(picinsidename) 

    text_file.close()

if __name__ == "__main__":
    main()

