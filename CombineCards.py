from PIL import Image

def main():

    numcards = 30

    for j in range(0,int(numcards/6)):

        #make big image to combine cards
        img = Image.new('RGBA', (1200, 1200), (255,255,255))

        for i in range(0,6):
            #Relative Path
            filename = "cards/card" + str(i+1+6*j) + ".png"
            cardimg = Image.open(filename)
            width, height = cardimg.size
    
            print("width =",width)
            print("height =",height)
    
            #paste photo
            if i%2==0:
                xpos = 0
            else:
                xpos = 600
            ypos = int(i/2)*400
            img.paste(cardimg,(xpos,ypos))
    
        #img.show()
    
        #Saved in the same relative location
        picname = "cards/combinedCards" + str(j) + ".png"
        print(picname)
        img.save(picname) 
 
if __name__ == "__main__":
    main()
