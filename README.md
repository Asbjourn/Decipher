# Decipher.py

Takes in an encoded (char swapped) file, a non encoded file to create a baseline off and attempts to decode

Optionally takes in the names of the output decoded and cipher files and the name of a whitespace delineated file of characters sorted highest to lowest in order of probablity of occurence in a word.  If such a file is not provided, the list is created using the baseline file.

# Use: Running in Python32

decipher.py -i \<encoded-file\> -b \<baseline-file\> [-o \<decoded-file\>] [-c \<cipher-file\>] [-f \<frequency-file\>]

