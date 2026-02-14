from layouts import *
import random

layouts = {"qwerty":qwerty,"dvorak":dvorak,"colemak":colemak,"workman":workman}
chosen = 0

chars = {}

def commonality(s): # Checks how common the letters in a word is for the list
    global chars
    score = 0
    for letter in s:
        score += chars[letter.lower()]
    
    if s =='' : return 0
    # print(s + " " + str(score/len(s))) 
    return score/len(s)


class Wordlist: # I don't know if we need a class here, but we do now
    global chars
    def __init__(self,layout="qwerty",rows=[1],min_length=3): # Rows is a list of the rows you want to include top: 0, middle: 1, bottom 2
        self.layout = layout
        # print(layout)
        # print(layouts[layout])
        self.rows = rows
        self.all_words = []
        self.included = ""
        self.min_length = min_length

        for row in self.rows:
            self.included += layouts[self.layout][row]
        
        with open("wordlists/top10k.txt") as words:
            for word in words.read().split('\n'):
                correct = True
                for letter in word.lower():
                    if letter not in chars:
                        chars[letter] = 1

                    else:
                        chars[letter] += 1
                    
                    if not letter in self.included:
                        correct = False
                
                if correct and len(word) >= self.min_length:
                    self.all_words.append(word)

        # self.all_words.sort(key=commonality) sorts words based on how common the letters in the word are, but it is not needed for our purposes and it is slow, so I commented it out

    def random(self,amount=10): # Generates a list of random words, amount being the amount
        return_words = []

        for i in range(amount):
            return_words.append(self.all_words[random.randint(0,len(self.all_words)-1)])
        
        return return_words

    def list(self):
        return

