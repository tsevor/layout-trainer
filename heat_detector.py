from layouts import *

homerow_words = []

layouts = [qwerty,dvorak,colemak,workman]
chosen = 0

row = {
    "home":1,
    "top":0,
    "bottom":2
}

chars = {}

def commonality(s):
    global chars
    score = 0
    for letter in s:
        score += chars[letter.lower()]
    
    if s =='' : return 0
    print(s + " " + str(score/len(s)))
    return score/len(s)


with open("wordlists/all-unfiltered.txt") as words:
    for word in words.read().split('\n'):
        correct = True
        for letter in word.lower():
            if letter not in chars:
                chars[letter] = 1

            else:
                chars[letter] += 1

            if not letter in layouts[chosen][row["home"]]: 
                correct = False
        
        if correct:
            homerow_words.append(word)

homerow_words.sort(key=commonality)
print(homerow_words[40:])