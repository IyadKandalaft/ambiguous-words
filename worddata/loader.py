# -*- coding: utf-8 -*-

from worddata.graph import Graph
import logging
import re

logger = logging.getLogger(__name__)

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
    word_graph = Graph()
    
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
            word_graph.add_node(primary_word)

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
                    word_graph.add_node(word)
                    word_graph.add_edge(primary_word, word)

            # Provide progress information
            line_num += 1
            if line_num % 100000 == 0:
                logger.debug("Processing word relations file %s line %d", file, line_num)

            if callable is not None and callable(line_callback):
                line_callback(word_graph)

            if reset_after_line:
                word_graph.clear()
    if line_num > 0:
        logger.info("Finished process word relations file %s. Total line count: %d", file, line_num)

    return word_graph

def generate_wordpacks(wordpacks_file, wordpack_title_format='^(### \d+ ###)', term_format='^@ ANT-([^=]+) =', wordlist_format='= (.+)( · )?$', wordlist_delim=' · '):
    '''
    A generator function that parses a file containing wordpacks and yields a 
    tuple providing the wordpack title and a dictionary of { "term": [ "word", "list" ] }
    
    e.g. wordpack file:
    ### 1 ###
    tree: maple · poplar · green
    dog: rover · canine · animal
    furniture: table · desk · chair
    ### 2 ###
    family: kids · parents · children
    community: houses · neighbours · parks · streets
    ### 3 ###
    ANT-friend: foe · fiend · alien

    Arguments:
        wordpack_file {str} -- Path to the file containing the wordpack groups
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