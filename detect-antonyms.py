#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from logging.config import dictConfig
import logging

from worddata.loader import generate_wordpacks, load_words_graph
from worddata.graph import Graph

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
    loggers = {
        'worddata.loader': {
            'handlers': ['h'],
            'level': logging.DEBUG,
        }
    },
    root = {
        'handlers': ['h'],
        'level': logging.DEBUG,
        }
)
dictConfig(logging_config)
logger = logging.getLogger()

args = None

def main():
    '''Main function that gets called when the script is executed'''
    
    args, parser = get_config()

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
        prog=__file__,
        description="Take word packs as input and output a file with the antonyms highlighted.",
        formatter_class=lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, width=120))

    parser.add_argument(
        "-w", "--wordpacks",
        metavar='PATH',
        required=True,
        help="Wordpacks file to use as input")
    parser.add_argument(
        "-r", "--relations",
        metavar='PATH',
        required=True,
        help="Word relations file to use as input")
    parser.add_argument(
        "-p", "--primary-word-regex",
        metavar='REGEX',
        required=False, 
        default="^#([^\[]+)",
        help="Regex to parse the list of words in the word relations file")
    parser.add_argument(
        "-a", "--antonym-regex",
        metavar='REGEX',
        required=False,
        default="\[(?:contrast-manual|contrast)=\d+\.\d+\]:([^;]+)",
        help="Regex to parse the list of antonyms in the word relations file")
    parser.add_argument(
        "-as", "--antonym-score-regex",
        required=False,
        metavar='REGEX',
        default="\[(?:contrast-manual|contrast)-score\]:([^;]+)",
        help="Regex to parse the score of antonyms in the word relations file")
    parser.add_argument(
        "-s", "--synonym-regex",
        required=False,
        metavar='REGEX',
        default='\[(?:syn|associated)[^=\]]*?=\d+\.\d+\]:([^;]+)',
        help="Regex to parse the list of synonyms in the word relations file")
    parser.add_argument(
        "-ss", "--synonym-score-regex",
        metavar='REGEX',
        required=False,
        default='\[(?:syn|associated).*?-score\]:([^;]+)',
        help="Regex to parse the score of synonyms in the word relations file")
    parser.add_argument(
        "-d", "--word-delimeter",
        metavar='CHAR',
        required=False,
        default="|",
        help="Delimiter to split the text matched by regex --antonym-regex into a list")
    parser.add_argument(
        "-c", "--score-cutoff",
        metavar='NUM',
        required=False,
        default="8.0",
        type=float,
        help="Eliminate synonyms that are below the provided value")
    parser.add_argument(
        "-o", "--output",
        metavar='PATH',
        required=False,
        default="output.txt",
        help="Highlighted antonyms output file path")

    return parser.parse_args(), parser

def get_ambiguous_antonyms(antonyms_graph:Graph, synonyms_graph:Graph, wordpack_dict:dict):
    '''Iterates through a wordpack and determines if a base term's related terms are antonyms of another base term in the wordpack.

    Consider a wordpack_dict as follows:

    {
        base_term1: [ antonym1, antonym2, antonym3 ],
        base_term2: [ antonym4, antonym5, antonym6 ]
    }

    If antonym3 is also an antonym of base_term2, then it's considered ambiguous

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
                    logger.info(f"Base term '{base_term}' and its related term '{related_term}' are ambiguous with base term group '{base_term2}'")
        
    return return_ds

if __name__ == "__main__":
    main()