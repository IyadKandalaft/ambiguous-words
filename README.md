# Synonym and Antonym Detection

## Table of Contents

- [About](#about)
- [Getting Started](#getting_started)
- [Usage](#usage)

## About <a name = "about"></a>

Takes a wordpack file and finds ambiguous synonyms or antonyms within a word pack.

e.g. Wordpack file:

```
### Word Pack 1 ###
@ base_term1 = synonym1 · synonym2
@ base_term2 = synonym3 · synonym4 · synonym6
@ base_term3 = synonym7 · synonym8
### Word Pack 2 ###
@ ANT-base_term1 = antonym1 · antonym2
@ ANT-base_term2 = antonym3 · antonym4 · antonym6
@ ANT-base_term3 = antonym7 · antonym8
```

Within Word Pack 2, if antonym3 is also an antonym of base_term1, then it's considered ambiguous
Within Word Pack 1, if synonym1 is also a synonym of base_term3, then it's considered ambiguous

## Getting Started <a name = "getting_started"></a>

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

Clone the code to your PC
```
git clone https://github.com/IyadKandalaft/ambiguous-words
cd ambiguous-words
```

Locate your wordpacks file and the word relationship data file. For this example, we'll assume they are named ~/wordpack.txt and ~/wordrelations.txt

Execute the detect-antonyms.py script
```
./detect-antonyms.py -w ~/wordpack.txt -r ~/wordrelations.txt --output ~/output.txt
```

Review the output
```
less output.txt
```

### Prerequisites

What things you need to install the software and how to install them.

```
Python 3.x
```

## Usage <a name = "usage"></a>

Each script has its own built-in help that can be printed using the @--help@ option.

### detect-antonyms.py

```
usage: detect-antonyms.py [-h] -w PATH -r PATH [-p REGEX] [-a REGEX] [-as REGEX] [-s REGEX] [-ss REGEX] [-d CHAR]
                          [-c NUM] [-o PATH]

Take word packs as input and output a file with the antonyms highlighted.

optional arguments:
  -h, --help            show this help message and exit
  -w PATH, --wordpacks PATH
                        Wordpacks file to use as input (default: None)
  -r PATH, --relations PATH
                        Word relations file to use as input (default: None)
  -p REGEX, --primary-word-regex REGEX
                        Regex to parse the list of words in the word relations file (default: ^#([^\[]+))
  -a REGEX, --antonym-regex REGEX
                        Regex to parse the list of antonyms in the word relations file (default: \[(?:contrast-
                        manual|contrast)=\d+\.\d+\]:([^;]+))
  -as REGEX, --antonym-score-regex REGEX
                        Regex to parse the score of antonyms in the word relations file (default: \[(?:contrast-manual|contrast)-score\]:([^;]+))
  -s REGEX, --synonym-regex REGEX
                        Regex to parse the list of synonyms in the word relations file (default: \[(?:syn-?[^=\]]+|associated-?[^=\]]+)=\d+\.\d+\]:([^;]+))
  -ss REGEX, --synonym-score-regex REGEX
                        Regex to parse the score of synonyms in the word relations file (default: \[(?:syn-?.*?|associated-?.*?)-score\]:([^;]+))
  -d CHAR, --word-delimeter CHAR
                        Delimiter to split the text matched by regex --antonym-regex into a list (default: |)
  -c NUM, --score-cutoff NUM
                        Eliminate synonyms that are below the provided value (default: 8.0)
  -o PATH, --output PATH
                        Highlighted antonyms output file path (default: output.txt)
```
