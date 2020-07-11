#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from graph import Graph
from logging.config import dictConfig
import logging
import re

# Setup logging
logging_config = dict(
    version = 1,
    formatters = {
        'f': {'format':
              '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'}
        },
    handlers = {
        'h': {'class': 'logging.StreamHandler',
              'formatter': 'f',
              'level': logging.DEBUG}
        },
    root = {
        'handlers': ['h'],
        'level': logging.DEBUG,
        },
)
dictConfig(logging_config)
logger = logging.getLogger()

args = None

def main():
    '''Main function that gets called when the script is executed'''
    
    args = get_config()

    # Create a graph of related antonyms from our data
    antonym_graph = load_words_graph(args.relations, args.primary_word_regex, args.antonym_regex, args.antonym_score_regex, args.word_delimeter)
    # Create a graph of related synonyms from our data
    synonym_graph = load_words_graph(args.relations, args.primary_word_regex, args.synonym_regex, args.synonym_score_regex, args.word_delimeter, args.score_cutoff)

    # Parse out the wordpack title and the groups of words in it
    wordpacks = generate_wordpacks(args.wordpacks)
    with open(args.output, 'w+') as fh:
        for (wordpack_title, wordpack_dict) in wordpacks:
            ambiguous_antonyms = get_ambiguous_antonyms(antonym_graph, synonym_graph, wordpack_dict)
            fh.write(wordpack_title + "\n")
            for base_term, related_terms in wordpack_dict.items():
                base_terms_overlap = ', '.join(set(ambiguous_antonyms[base_term]['overlap']))
                if base_terms_overlap:
                    fh.write(f"[ {base_terms_overlap} ] @ ANT-{base_term} = ")
                else:
                    fh.write(f"@ ANT-{base_term} = ")

                output = ""
                for related_term in related_terms:
                    if related_term in ambiguous_antonyms[base_term]['related_terms']:
                        term_index = ambiguous_antonyms[base_term]['related_terms'].index(related_term)
                        matching_base_term = ambiguous_antonyms[base_term]['overlap'][term_index]
                        output = output + f"[ {matching_base_term} : {related_term} ]" + " · "
                        continue
                    
                    output = output + related_term + " · "
                output = output[:-3] + "\n"
                fh.write(output)

        #break

def get_config():
    '''
    Defines the command line parameters and returns the parameters passed to the script

    Returns:
        argparse.args -- An object containing the parsed command line parameters
    '''
    parser = argparse.ArgumentParser(
        prog='highlight-antonyms.py',
        description="Take word packs as input and output a file with the antonyms highlighted.")

    parser.add_argument(
        "-w", "--wordpacks",
        required=True,
        help="Wordpacks file to use as input")
    parser.add_argument(
        "-r", "--relations",
        required=True,
        help="Word relations file to use as input")
    parser.add_argument(
        "-p", "--primary-word-regex",
        required=False, 
        default="^#([^\[]+)",
        help="Regex to parse the list of words in the word relations file")
    parser.add_argument(
        "-a", "--antonym-regex",
        required=False,
        default="\[(?:contrast-manual|contrast)=\d+\.\d+\]:([^;]+)",
        help="Regex to parse the list of antonyms in the word relations file")
    parser.add_argument(
        "-as", "--antonym-score-regex",
        required=False,
        default="\[(?:contrast-manual|contrast)-score\]:([^;]+)",
        help="Regex to parse the score of antonyms in the word relations file")
    parser.add_argument(
        "-s", "--synonym-regex",
        required=False,
        default="\[(?:syn|syn-[^=\]]+)=\d+\.\d+\]:([^;]+)",
        help="Regex to parse the list of synonyms in the word relations file")
    parser.add_argument(
        "-ss", "--synonym-score-regex",
        required=False,
        default="\[(?:syn|syn-.*?)-score\]:([^;]+)",
        help="Regex to parse the score of synonyms in the word relations file")
    parser.add_argument(
        "-d", "--word-delimeter",
        required=False,
        default="|",
        help="Delimiter to split the text matched by regex --antonym-regex into a list")
    parser.add_argument(
        "-c", "--score-cutoff",
        required=False,
        default="5.0",
        type=float,
        help="Eliminate synonyms that are below the provided value")
    parser.add_argument(
        "-o", "--output",
        required=False,
        default="output.txt",
        help="Highlighted antonyms output file path")

    return parser.parse_args()

def load_words_graph(file:str, primary_word_parser:str, words_parser:str, 
                score_parser:str, word_delimiter:str='|', score_cutoff:float = 1,
                line_callback:callable=None, reset_after_line=False):
    """Creates a graph of antonym words from a file where the words are
    on one line and separated by delimeters

    Arguments:
        file {str} -- The file to load into 
        primary_word_parser {str} -- Regular expression used to parse the primary word in data file
        words_parser {str} -- Regular expression used to parse the related words
        score_parser {str} -- Regular expression used to parse the scores of related words
        word_delimeter {str} -- Regular expression used to split the group returned by the 'words_parser' regex into words
        line_callback {Callable} -- Class or function called after each line is processed and passed in the graph
        reset_after_line {bool} -- Clears the graph after each line is processed
    
    Returns:
        Graph -- A graph object that permits traversal between the antonyms
    """
    antonyms_graph = Graph()
    
    primary_word_regex = re.compile(primary_word_parser)
    words_regex = re.compile(words_parser)
    score_regex = re.compile(score_parser)

    with open(file, 'r') as fh:
        line_num = 0
        
        for line in fh:
            matches = primary_word_regex.match(line) 
            # Skip line if we can't parse the primary word
            if ( matches == None ):
                logger.warn(f"Primary word not found on line {line_num}")
                continue

            primary_word = matches.group(1)
            antonyms_graph.add_node(primary_word)

            score_matches = score_regex.finditer(line)

            # Get the antonym section of the line
            words = ''
            for word_match in words_regex.finditer(line):
                # Split the first matched group into separate words
                words = word_match.group(1).split(word_delimiter)

                # Get the associated scores for each word
                try:
                    word_scores = next(score_matches).group(1).split(word_delimiter)
                except StopIteration:
                    logger.warn(f"Unable to parse scores for line {line_num} using regex {score_parser}")

                # Remove empty values in the list, new lines, and words that contain numbers (if any)
                #words = [x for x in words if x != '' and _hasAlphaOnly(x)]

                word_scores_iter = iter(word_scores)
                
                for word in words:
                    try:
                        score = float(next(word_scores_iter))
                    except StopIteration:
                        logger.warn(f"{primary_word}'s related Word '{word}' does not have a matching score")

                    if score < score_cutoff:
                        continue
                    antonyms_graph.add_node(word)
                    antonyms_graph.add_edge(primary_word, word)

            # Provide progress information
            line_num += 1
            if line_num % 100000 == 0:
                logger.debug("Processing word relations file %s line %d", file, line_num)

            if callable is not None and callable(line_callback):
                line_callback(antonyms_graph)

            if reset_after_line:
                antonyms_graph.clear()
    if line_num > 0:
        logger.info("Finished process word relations file %s. Total line count: %d", file, line_num)

    return antonyms_graph

def get_ambiguous_antonyms(antonyms_graph:Graph, synonyms_graph:Graph, wordpack_dict:dict):
    '''Iterates through a wordpack and determines if a base term's related terms are antonyms of another base term in the wordpack.

    Consider a wordpack_dict as follows:

    {
        base_term1: [ antonym1, antonym2, antonym3 ],
        base_term2: [ antonym4, antonym5, antonym6 ]
    }

    If antonym3 is also an antonym of base_term2, then it's considered an ambiguous antonym

    Arguments:
        graph {Graph} -- A graph of antonyms
        wordpack_dict {dict} -- A wordpack encapsulated within a dictionary object where keys are the base terms and their value is a list of related terms
    '''
    # Data structure that will be returned 
    return_ds = {}
    for base_term, related_terms in wordpack_dict.items():
        # Create a datastructure to track matches
        return_ds[base_term] = {
            'overlap': [],
            'related_terms': []
            }

        for base_term2, related_terms2 in wordpack_dict.items():
            # Don't compare the same group of words
            if ( base_term == base_term2 ): continue
            # Check if we have antonyms for base_term2 in the graph
            if base_term2 not in antonyms_graph.nodes: continue

            # Get the antonyms of base_term2
            antonyms = list(antonyms_graph.nodes[base_term2].neighbors.keys())
            for antonym in list(antonyms_graph.nodes[base_term2].neighbors.keys()):
                if antonym not in synonyms_graph.nodes:
                    continue
                synonyms = list(synonyms_graph.nodes[antonym].neighbors.keys())
                antonyms.extend(synonyms)

            for related_term in related_terms:
                if ( related_term in antonyms ):
                    return_ds[base_term]['overlap'].append(base_term2)
                    return_ds[base_term]['related_terms'].append(related_term)
                    logger.debug(f"Base term '{base_term}' and its related term '{related_term}' are ambiguous with base term group '{base_term2}'")
        
    return return_ds

def generate_wordpacks(wordpacks_file, wordpack_title_format='^(### \d+ ###)', term_format='^@ ANT-([^=]+) =', wordlist_format='= (.+)( · )?$', wordlist_delim=' · '):
    '''
    A generator function that parses a file containing wordpacks and yields a 
    tuple providing the wordpack title and a dictionary of { "term": [ "word", "list" ] }
    
    e.g. wordpack file:
    ### 1 ###
    tree: maple, poplar, green
    dog: rover, canine, animal
    furniture: table, desk, chair
    ### 2 ###
    family: kids, parents, children
    community: houses, neighbours, parks, streets

    Arguments:
        wordpack_file {str} -- A file containing the wordpack groups
        wordpack_title_format {str} -- A regex to parse the wordpack title in group 1
        term_format {str} -- A regex to parse the base term in each term group in group 1
        wordlist_format {str} -- A regex to parse the related terms to the base term in group 1
        wordlist_delim {str} -- A delimeter used to split the wordlist into a list
    
    Yields:
        tuple(str, dict) -- A tuple of the Wordpack title and a dictionary of grouped terms where the key is the base term
    '''
    wordpack_title_re = re.compile(wordpack_title_format)
    term_re = re.compile(term_format)
    wordlist_re = re.compile(wordlist_format)

    logger.info("Processing wordpack file %s", wordpacks_file)
    with open(wordpacks_file, 'r') as fh:       
        wordpack_title = None
        wordpack_dict = {}
        for line in fh:           
            matches = wordpack_title_re.search(line)
            if ( matches != None ):
                if ( wordpack_title != None and wordpack_dict ):
                    # Yield previously identified wordpack title and its terms using the defined data structure
                    yield wordpack_title, wordpack_dict
                
                wordpack_title = matches.group(1).strip()
                wordpack_dict = {}
                
                logger.debug("Processing wordpack titled '%s'", wordpack_title)
                
                continue
         
            # Continue if we haven't found the start of a wordpack
            if ( wordpack_title is None ): continue
            
            # Get the main term
            matches = term_re.search(line)
            if ( matches == None ): continue
            term = matches.group(1).strip()

            # Get the term's wordlist
            matches = wordlist_re.search(line)
            if ( matches == None ): continue
            wordlist = matches.group(1).strip().split(wordlist_delim)

            wordpack_dict[term] = wordlist

        if ( wordpack_title != None and wordpack_dict):
            yield wordpack_title, wordpack_dict

def _hasAlphaOnly(input):
    '''
    Determines if the input contains alpha characters and spaces

    Returns:
        bool - True if the input contains only alpha charactesr and spaces or False otherwise
    '''
    return bool(re.search(r'^[A-z ]+$', input))

if __name__ == "__main__":
    main()