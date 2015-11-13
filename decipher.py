#!/usr/bin/python
import sys
import re
import getopt

# Global variables
chars_lower = set([ 'a', 'b', 'c', 'd', 'e',
                    'f', 'g', 'h', 'i', 'j',
                    'k', 'l', 'm', 'n', 'o',
                    'p', 'q', 'r', 's', 't',
                    'u', 'v', 'w', 'x', 'y', 'z' ])

# Functions
def insert_char(sorted_chars, char_occurences, char):
    """
    Inserts char into the current list of sorted chars, highest to lowest
    Does not check for prior existence
    Weights are the number of occurences of a char, given by char_occurences
    
    This function is used in sort_char_occurences to create a sorted list of all seen chars

    @type sorted_chars list
    @param sorted_chars A list of chars sorted highest to lowest
    @type char_occurences dict
    @param char_occurences A dict [char:int] mapping a char to the number of occurences
    @type char char
    @param char The character to insert into the list
    """
    char_length = len(sorted_chars)
    if char_length == 0:
        sorted_chars.append(char)
        return
    marker_start = 0
    marker_end = char_length - 1
    flag = True
    
    while flag:
        if marker_start == marker_end:
            if char_occurences[sorted_chars[marker_start]] > char_occurences[char]:
                marker_start += 1
                flag = False
                break
            else:
                flag = False
                break
        
        marker_test = (int)((marker_start + marker_end) / 2)
        if char_occurences[sorted_chars[marker_test]] > char_occurences[char]:
            marker_start = marker_test + 1
        else:
            if marker_start == marker_test:
                flag = False
                break
            else:
                marker_end = marker_test - 1

    sorted_chars.insert(marker_start, char)

def sort_char_occurences(char_occurences):
    """
    Creates a list of chars sorted by number of occurences (highest to lowest)
    @type char_occurences dict
    @param char_occurences A dict [char:int] mapping a char to the number of occurences
    """
    sorted_chars = []
    for char in char_occurences:
        insert_char(sorted_chars, char_occurences, char)
    return sorted_chars

def try_substitution(char_map, char, sub, char_word_map, dictionary_str):
    """
    Attempts to perform regex maps with dictionary with the given substitutions
    Returns true is 80% or more of words have matches
    
    This function is used in regex_search to test a proposed character substitution

    @type char_map dict
    @param char_map A dict [char:char] of the currently mapped cipher chars
    @type char char
    @param char The char to attempt to map
    @type sub char
    @param sub The proposed map of char
    @type char_word_map dict
    @param char_word_map A dict [char:set([string])] mapping a character to a set of all cipher words containing that character
    @type dictionary_str dict
    @param dictionary_str A dict [int:string] mapping a word length to a '.'join() string of all baseline words of that length
    """
    ### 
    words_to_match = []
    words_length = []
    matched = 0

    # Create regex strings to match
    for word in char_word_map[char]:
        regex = r'\b'
        count = 0
        for i in range(0, len(word)):
            if word[i] in char_map:
                if count > 0:
                    regex += '[a-z]{' + str(count) + '}'
                    count = 0
                regex += '[' + char_map[word[i]] + char_map[word[i]].upper() + ']'
            elif word[i] == char:
                if count > 0:
                    regex += '[a-z]{' + str(count) + '}'
                    count = 0
                regex += '[' + sub + sub.upper() + ']'                
            else:
                count += 1

        if count > 0:
            regex += '[a-z]{' + str(count) + '}'
        regex += r'\b'
        words_to_match.append(regex)
        words_length.append(len(word))


    # Search for matches in dictionary
    for i in range(0, len(words_to_match)):
        word = words_to_match[i]
        word_length = words_length[i]
        if word_length in dictionary_str:
            match = re.search(word, dictionary_str[word_length].lower())
            if match:
                matched += 1

    if float(matched)/float(len(words_to_match)) > 0.8:
        return True
    else:
        return False
        
def regex_search(char_map, cipher_char_frequency, base_char_frequency, char_word_map, dictionary_str):
    """
    Regex search, recursively attempting substitutions and checking results in dictionaries
    
    Returns true if a full char_map is found (all cipher chars have been mapped).
    Returns false if all possibilities have been exhausted and not all cipher chars have been mapped.

    @type char_map dict
    @param char_map A dict [char:char] of the currently mapped cipher chars
    @type cipher_char_frequency list
    @param cipher_char_frequency A list of all seen cipher chars sorted in order of highest to lowest occurence
    @type base_char_frequency list
    @param base_char_frequency A list of all seen base chars sorted in order of highest to lowest occurence
    @type char_word_map dict
    @param char_word_map A dict [char:set([string])] mapping a character to a set of all cipher words containing that character
    @type dictionary_str dict
    @param dictionary_str A dict [int:string] mapping a word length to a '.'join() string of all baseline words of that length
    """
    # Determine the char to substitute, we'll pick the largest occuring char in the cipher that isn't already mapped
    char = ''
    for x in cipher_char_frequency:
        if x not in char_map:
            char = x
            break;
        
    if char == '':
        return False

    # Attempt to substitute, we'll go in order of the statistically largest occuring char that isn't already mapped
    for x in base_char_frequency:
        if x not in char_map.values():
            # Test substitution
            result = try_substitution(char_map, char, x, char_word_map, dictionary_str)
            if result:
                # Update char_map with potential
                char_map[char] = x
                if len(char_map) == len(cipher_char_frequency):
                    # We're done!
                    return True
                else:
                    # Recurse down
                    result = regex_search(char_map, cipher_char_frequency, base_char_frequency, char_word_map, dictionary_str)
                    if result:
                        return True
                    else:
                        del char_map[char]

    return False

def process_base_file(base_file_name, dictionary, char_occurences=None, frequency_set=False):
    """
    Opens the baseline file and, line by line, updates a dictionary of legal words.
    Optionally attempts to update a dict of baseline character occurences

    @type base_file_name string
    @param base_file_name The name of the baseline file to open
    @type dictionary dict
    @param dictionary A dict [int:set([string])] mapping word lengths to a set of all baseline words of that length
    @type char_occurences dict
    @param char_occurences A dict [char:int] mapping baseline chars seen to the number of occurences
    @type frequency_set bool
    @param frequency_set A bool dictating whether a frequency file was provided (i.e. used to determine whether char_occurences should be updated)
    """
    ### Process base file, updating a dict of legal words and optionally updating a dict of character occurences
    # Open base file
    try:
        base_file = open(base_file_name, 'r', encoding='utf-8')
    except IOError as e:
        print('Failed to open base file:\n{0}'.format(e))
        sys.exit(0)

    flag = True
    while(flag):
        content = base_file.readline()
        if content == '':
            flag = False
        else:
            dictionary_from_content(content, dictionary)
            if not frequency_set:
                if char_occurences != None:
                    temp_char_occurences = count_char(content)
                    for char in temp_char_occurences:
                        if char not in char_occurences:
                            char_occurences[char] = 0
                        char_occurences[char] += temp_char_occurences[char]
    # Close base file
    base_file.close()

def dictionary_from_content(content, dictionary):
    """
    Given a string, updates a dictionary of legal words.

    @type content string
    @param content A string of legal words
    @type dictionary dict
    @param dictionary A dict [int:set([string])] mapping word lengths to a set of all baseline words of that length
    """
    ### Process content to add to dictionary of length mappings
    match = re.findall(r'\b[a-zA-Z]+\b', content)
    if len(match) > 0:
        for word in match:
            word_length = len(word)
            # Add to appropriate dictionary
            if word_length not in dictionary:
                dictionary[word_length] = set([])
            dictionary[word_length].add(word)

def process_frequency_file(frequency_file_name):
    """
    Read a text file containing a whitespace delineated list of chars in order of decreasing probability of occuring in a word
    Creates and returns a list of characters sorted highest to lowest

    @type frequency_file_name string
    @param frequency_file_name The name of the text file
    """
    global char_frequency_default
    char_frequency = []
    try:
        frequency_file = open(frequency_file_name, 'r', encoding='utf-8')
    except IOError as e:
        print('Failed to open frequency file: {0}.'.format(frequency_file_name))
        return char_frequency

    frequency_content = frequency_file.read()
    frequency_file.close()
    for char in frequency_content:
        if char in chars_lower:
            char_frequency.append(char)
    return char_frequency

def count_char(string):
    """
    Process a string to create a dict [char:int] of how many times a character occurs
    Returns the dictionary

    @type string string
    @param string The string to process
    """
    char_occurences = {}
    string_lower = string.lower()
    for i in range(0, len(string_lower)):
        char_lower = string_lower[i]
        if char_lower in chars_lower:
            if char_lower not in char_occurences:
                char_occurences[char_lower] = 0
            char_occurences[char_lower] = char_occurences[char_lower] + 1
    return char_occurences

def map_char_word(string):
    """
    Process a string to create a dict [char:set([string])] of characters to words containing the character
    Returns the dictionary

    @type string string
    @param string The string to process
    """
    char_word_map = {}
    string_lower = string.lower()
    start_marker = 0
    start_word = False
    for i in range(0, len(string_lower)):
        char_lower = string_lower[i]
        if char_lower in chars_lower:
            if not start_word:
                start_marker = i
                start_word = True
        else:
            if start_word:
                word_lower = string_lower[start_marker:i]
                # Add word to char_word map
                for char in word_lower:
                   if char not in char_word_map:
                       char_word_map[char] = set([])
                   char_word_map[char].add(word_lower)
                start_word = False
    return char_word_map

def map_word_length(string):
    """
    Process a string to create a dict [int:list[string]] of word lengths to cipher words
    Returns the dictionary

    @type string string
    @param string The string to process
    """
    ### 
    word_length_map = {}
    start_marker = 0
    start_word = False
    for i in range(0, len(string)):
        char_lower = string[i].lower()
        if char_lower in chars_lower:
            if not start_word:
                start_marker = i
                start_word = True
        else:
            if start_word:
                word = string[start_marker:i]
                word_length = len(word)
                # Add word to word_length_map
                if word_length not in word_length_map:
                   word_length_map[word_length] = []
                if word not in word_length_map[word_length]:
                    word_length_map[word_length].append(word)
                start_word = False
    return word_length_map

def find_a_i(word_length_map):
    """
    Attempt to find 'a' and/or 'i' based on word length and capitalization
    Returns a dict [char:char} charmap of values found

    @type word_length_map dict
    @param word_length_map A dict [int:list[string]] mapping word lengths to a list of cipher words of that length
    """
    # There are only two letters that can stand alone, 'a' and 'i'
    # 'i' must be capitalized no matter what, so if there is a char that is not capitalized, we've found 'a'
    char_map = {}
    if 1 in word_length_map:
        if len(word_length_map[1]) == 2:
            if word_length_map[1][0].islower():
                # $0 is 'a', $1 is 'i'
                char_map[word_length_map[1][0]] = 'a'
                char_map[word_length_map[1][1].lower()] = 'i'
            elif word_length_map[1][1].islower():
                # $0 is 'i', $1 is 'a'
                char_map[word_length_map[1][0].lower()] = 'i'
                char_map[word_length_map[1][1]] = 'a'
        elif len(word_length_map[1]) == 1:
            if word_length_map[1][0].islower():
                # $0 is 'a'
                char_map[word_length_map[1][0]] = 'a'
    return char_map
    
def main(argv):
    global char_frequency_default
    input_file_name = ''
    base_file_name = ''
    output_file_name = 'decoded.txt'
    output_set = False
    cipher_file_name = 'cipher.txt'
    cipher_set = False
    frequency_file_name = ''
    frequency_set = False
    char_frequency = []
    try:
        opts, args = getopt.getopt(argv, "hi:b:o:c:f:",["ifile=", "bfile=", "ofile=", "cfile=", "ffile="])
    except getopt.GetoptError:
        print('decipher.py -i <encoded-file> -b <baseline-file> [-o <decoded-file>] [-c <cipher-file>] [-f <frequency-file>]')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print('decipher.py -i <encoded-file> -b <baseline-file> [-o <decoded-file>] [-c <cipher-file>] [-f <frequency-file>]')
            sys.exit(0)
        elif opt in ("-i", "--ifile"):
            input_file_name = arg
        elif opt in ("-b", "--bfile"):
            base_file_name = arg
        elif opt in ("-o", "--ofile"):
            output_file_name = arg
            output_set = True
        elif opt in ("-c", "--cfile"):
            cipher_file_name = arg
            cipher_set = True
        elif opt in ("-f", "--ffile"):
            frequency_file_name = arg
            frequency_set = True

    if input_file_name == '':
        print('decipher.py -i <encoded-file> -b <baseline-file> [-o <decoded-file>] [-c <cipher-file>] [-f <frequency-file> ]')
        sys.exit()
    if base_file_name == '':
        print('decipher.py -i <encoded-file> -b <baseline-file> [-o <decoded-file>] [-c <cipher-file>] [-f <frequency-file> ]')
        sys.exit()
    print('Outputting decoded text to: {0}'.format(output_file_name))
    print('Outputting cipher to: {0}'.format(cipher_file_name))
    if not frequency_set:
        print('Building char frequency set from baseline file')
    else:
        char_frequency = process_frequency_file(frequency_file_name)
        if len(char_frequency) == 0:
            print('Building char frequency set from baseline file')
            frequency_set = False

    # Open and read cipher file
    try:
        input_file = open(input_file_name, 'r', encoding='utf-8')
    except IOError as e:
        print('Failed to open input file: {0}'.format(e))
        sys.exit(0)
        
    input = input_file.read()    
    # Close input file
    input_file.close()

    # Create map of cipher char occurences
    cipher_char_occurences = count_char(input)
    
    # Create list of cipher chars sorted by number of occurences (highest to lowest)
    sorted_cipher_chars = sort_char_occurences(cipher_char_occurences)
    
    # Create map of cipher chars to containing cipher words
    char_word_map = map_char_word(input)

    # Process base file to create length->list[string] mapped dictionaries
    # And potentially a dict of char occurences
    dictionary = {}
    normal_char_occurences = {}
    process_base_file(base_file_name, dictionary, normal_char_occurences, frequency_set)
    if not frequency_set:
        sorted_normal_chars = sort_char_occurences(normal_char_occurences)
    
    # Convert into length->concatenated.string dictionaries
    dictionary_str = {}
    for maps in dictionary:
        joined = ' '.join(dictionary[maps])
        dictionary_str[maps] = joined
    
    # Create map of cipher word lengths to cipher words
    word_length_map = map_word_length(input)
    
    char_map = {}
    
    # Search for 'a' and 'i'
    a_i = find_a_i(word_length_map)
    for char in a_i:
        char_map[char] = a_i[char]

    # Search
    if regex_search(char_map, sorted_cipher_chars, sorted_normal_chars, char_word_map, dictionary_str):
        # Open and write cipher file
        try:
            cipher_file = open(cipher_file_name, 'w', encoding='utf-8')
        except IOError as e:
            print('Failed to open cipher file: {0}'.format(e))
            sys.exit(0)
            
        for char in char_map:
            cipher_file.write('{0} : {1}\n'.format(char, char_map[char]))
        # Close cipher file
        cipher_file.close()

        # Create output text
        # Allocate all necessary memory at once i.e. no appending
        output = [' '] * len(input)
        for i in range(0, len(input)):
            # Check if character substitution needed
            if input[i].lower() in char_map:
                # Preserve case
                if input[i].isupper():
                    output[i] = char_map[input[i].lower()].upper()
                else:
                    output[i] = char_map[input[i]]
            else:
                output[i] = input[i]

        # Open and write output file
        try:
            output_file = open(output_file_name, 'w', encoding='utf-8')
        except IOError as e:
            print('Failed to open output file: {0}'.format(e))
            sys.exit(0)
        output_file.write(''.join(output))
        # Close output file
        output_file.close()
        print('Cipher found')
        sys.exit(0)
    else:
        print('Cipher not found')
        sys.exit(0)    
        
if __name__ == "__main__":
    main(sys.argv[1:])
