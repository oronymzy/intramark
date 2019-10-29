#!/usr/bin/python3
from collections import defaultdict
import argparse
import json
import os
import os.path
import re
import sys
import tempfile
import textwrap


# Creating temporary file to hold information from command line input
temporary_json_file_containing_information_from_command_line_input = tempfile.TemporaryFile('w+')
# Creating temporary file to hold markup for the entire document
temporary_json_file_containing_document_markup_entire = tempfile.TemporaryFile('w+')

def get_link_label_position(dictionary_key_string):
    """Get the position of a reference-style link label from a dictionary-key string, returning the position in list format.
    
    The link label's position is stored with 3 comma-separated numbers that indicate a link label's *line number*, *left bracket index*, and *right bracket index*. The numbers are stored in the following way: ["1,2,3"]
    
    The key is stored as a string instead of a list or a tuple because:
    
    1. Python does not support lists as dictionary keys.
    2. JSON does not support tuples as dictionary keys.
    """
    
    link_label_position = [ int(list_item) for list_item in dictionary_key_string.split(',') ]
    return link_label_position

def initial_input():
    """Get user input in the form of command line arguments, storing provided information in a dictionary.
    
    The `cli_ctrlflw` dictionary holds command-line-related information in the following way:
    
    ```yaml
    decrease_overall_heading_level_maximally: false                        # an item with a boolean value indicating if the overall heading level should be decreased maximally
    decrease_overall_heading_level_numerically: false                      # an item with a boolean value indicating if the overall heading level should be decreased by a numerical amount
    number_of_heading_levels_to_decrease_numerically: 0                    # an item with a numerical value indicating the number of heading levels to decrease numerically
    increase_overall_heading_level_numerically: false                      # an item with a boolean value indicating if the overall heading level should be increased by a numerical amount
    number_of_heading_levels_to_increase_numerically: 0                    # an item with a numerical value indicating the number of heading levels to increase numerically
    modification_to_be_made: false                                         # an item with a boolean value indicating if changes should be made to the contents of the file
    input_filename: foo.bar                                                # an item with a string value indicating the filename of the file to be used for input
    executing_from_terminal: false                                         # an item with a boolean value indicating if the program is executing from a terminal
    strip_trailing_number_signs_from_headings: false                       # an item with a boolean value indicating if the heading trailing number sign count should be equalized with heading level
    equalize_heading_trailing_number_sign_count_with_heading_level: false  # an item with a boolean value indicating if trailing number signs should be stripped from headings
    strip_all_heading_markup: false                                        # an item with a boolean value indicating if all heading markup text should be stripped
    strip_all_line_breaks: false                                           # an item with a boolean value indicating if all line break markup text should be stripped
    modification_to_be_made_to_heading: false                              # an item with a boolean value indicating if changes should be made to a heading
    modification_to_be_made_to_line_break: false                           # an item with a boolean value indicating if changes should be made to a line break
    ```
    """
    
    def specify_arguments():
        "Specify allowed command-line arguments using *argparse* module."
        
        parser = argparse.ArgumentParser(description="Analyze and modify Markdown-formatted text on the level of Markdown elements to make widespread changes to the text.",prefix_chars='-+=', formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument("filename", help="Filename for input.", default=None)
        parser.add_argument("-d", "--diagnostic", help="Display diagnostic information on the provided input instead of providing output.", action="store_true")
        parser.add_argument("-w", "--write-in-place", help="Overwrite input file.", action="store_true")
        modification_group = parser.add_argument_group('modification arguments', 'By default, the relative hierarchical differences between headings will be preserved.')
        modification_group.add_argument("-A", "--annotate", help=textwrap.dedent("""\
                                                            Display explanatory text about markup instead of displaying the markup itself.
                                                            - Use *H* to affect headings."""), default=None)
        modification_group.add_argument("+H", dest="plus_H", help=textwrap.dedent("""\
                                                            Increase overall heading level by either:
                                                            - a numerical amount from 1 to 5, or
                                                            - *max* for maximum allowable amount"""), default=None)
        modification_group.add_argument("-H", dest="minus_H", help=textwrap.dedent("""\
                                                            Decrease overall heading level by either:
                                                            - a numerical amount from 1 to 5, or
                                                            - *max* for maximum allowable amount."""), default=None)
        modification_group.add_argument("=H", dest="equals_H", help="Equalize heading trailing number sign count with heading level.", action="store_true")
        modification_group.add_argument("-k", "--link", help=textwrap.dedent("""\
                                                        Modify links.
                                                        - Use *i* to make all links inline-style. Link reference definitions are removed by default, but this behavior can be suppressed by adding *p* to preserve them."""), default=None)
        modification_group.add_argument("-s", "--strip", help=textwrap.dedent("""\
                                                        Strip away markup text.
                                                        - Use *b* to strip line breaks.
                                                        - Use *H* to strip all heading markup text.
                                                        - Use *H-end* to strip only trailing number signs and spaces from headings."""), default=None)
        mutually_exclusive_modification_group = modification_group.add_mutually_exclusive_group()
        mutually_exclusive_modification_group.add_argument("--heading-decrease-max", help="Decrease overall heading level by maximum allowable amount.", action="store_true")
        mutually_exclusive_modification_group.add_argument("--heading-increase-max", help="Increase overall heading level by maximum allowable amount.", action="store_true")
        args = parser.parse_args()
        return args, parser
    
    args, parser = specify_arguments()

    def assess_arguments(args, parser):
        "Determine if values provided by the user are valid, and assign values to control-variables, whether provided by the user or not."
        
        cli_ctrlflw = {} # dictionary to hold command-line-related, control-flow-affecting information

        # Assignments to hold default values for maximizing output consistency
        cli_ctrlflw["modification_to_be_made"] = False
        cli_ctrlflw["modification_to_be_made_to_heading"] = False
        cli_ctrlflw["modification_to_be_made_to_line_break"] = False
        cli_ctrlflw["modification_to_be_made_to_link"] = False

        def diagnostic_choice(args):
            "Affect control flow to display diagnostic information in place of file contents if the '--diagnostic' argument is provided."
            
            display_file_contents = True
            if args.diagnostic == True:
                diagnostic = True
                display_file_contents = False
            else:
                diagnostic = False
            return diagnostic, display_file_contents
        
        cli_ctrlflw["diagnostic"], cli_ctrlflw["display_file_contents"] = diagnostic_choice(args)

        def write_in_place_choice(args):
            "Affect control flow to overwrite input file if the '--write-in-place' argument is provided."
            
            if args.write_in_place == True:
                write_in_place = True
            else:
                write_in_place = False
            return write_in_place
        
        cli_ctrlflw["write_in_place"] = write_in_place_choice(args)

        def annotation_choice(args, parser):
            "Affect control flow to display explanatory text about an element instead of the element itself if the '--annotate' argument is provided, also performing data validation to ensure acceptable values are used."
            
            annotate_headings = False
            if args.annotate == "H":
                annotate_headings = True
            elif args.annotate != None:
                print("\nInvalid input:".upper(),"the only acceptable value for *-A/--annotate* is *H*.\n")
                parser.print_help()
                exit()
            return annotate_headings
        
        cli_ctrlflw["annotate_headings"] = annotation_choice(args, parser)
        
        def heading_increase_choice(args, parser):
            """Affect control flow to increase overall heading level.
            
            Heading can be increased maximally or numerically. If increased numerically, a string specifying the number of heading levels to be increased is received from user input, converted to an integer value, and validated.
            """
            
            if args.heading_increase_max == True or args.plus_H == "max":
                increase_overall_heading_level_maximally = True
            else:
                increase_overall_heading_level_maximally = False

            if args.plus_H != None and args.plus_H != "max":
                if args.plus_H.isdigit() and int(args.plus_H) >= 1 and int(args.plus_H) <= 5:
                    increase_overall_heading_level_numerically = True
                    number_of_heading_levels_to_increase_numerically = int(args.plus_H)
                else:
                    print("\nInvalid input:".upper(),"acceptable values for *+H* are *max* or *1-5*.\n")
                    parser.print_help()
                    exit()
            else:
                increase_overall_heading_level_numerically = False
                number_of_heading_levels_to_increase_numerically = 0
            
            return increase_overall_heading_level_maximally, increase_overall_heading_level_numerically, number_of_heading_levels_to_increase_numerically
        
        cli_ctrlflw["increase_overall_heading_level_maximally"], cli_ctrlflw["increase_overall_heading_level_numerically"], cli_ctrlflw["number_of_heading_levels_to_increase_numerically"] = heading_increase_choice(args, parser)

        def heading_decrease_choice(args, parser):
            """Affect control flow to decrease overall heading level.
            
            Heading can be decreased maximally or numerically. If decreased numerically, a string specifying the number of heading levels to be decreased is received from user input, converted to an integer value, and validated.
            """
            
            if args.heading_decrease_max == True or args.minus_H == "max":
                decrease_overall_heading_level_maximally = True
            else:
                decrease_overall_heading_level_maximally = False
            
            if args.minus_H != None and args.minus_H != "max":
                if args.minus_H.isdigit() and int(args.minus_H) >= 1 and int(args.minus_H) <= 5:
                    decrease_overall_heading_level_numerically = True
                    number_of_heading_levels_to_decrease_numerically = int(args.minus_H)
                else:
                    print("\nInvalid input:".upper(),"acceptable values for *-H* are *max* or *1-5*.\n")
                    parser.print_help()
                    exit()
            else:
                decrease_overall_heading_level_numerically = False
                number_of_heading_levels_to_decrease_numerically = 0
            
            return decrease_overall_heading_level_maximally, decrease_overall_heading_level_numerically, number_of_heading_levels_to_decrease_numerically
        
        cli_ctrlflw["decrease_overall_heading_level_maximally"], cli_ctrlflw["decrease_overall_heading_level_numerically"], cli_ctrlflw["number_of_heading_levels_to_decrease_numerically"] = heading_decrease_choice(args, parser)

        def heading_equalize_choice(args, parser):
            "Affect control flow to equalize heading trailing number sign count with heading level."
            
            if args.equals_H == True:
                equalize_heading_trailing_number_sign_count_with_heading_level = True
            else:
                equalize_heading_trailing_number_sign_count_with_heading_level = False
            return equalize_heading_trailing_number_sign_count_with_heading_level
        
        cli_ctrlflw["equalize_heading_trailing_number_sign_count_with_heading_level"] = heading_equalize_choice(args, parser)
        
        def strip_choice(args, parser):
            """Affect control flow to strip away markup text.
            
            - Use *b* to strip line breaks.
            - Use *H* to strip all heading markup text.
            - Use *H-end* to strip only trailing number signs and spaces from headings.
            """
            
            strip_trailing_number_signs_from_headings = False
            strip_all_heading_markup = False
            strip_all_line_breaks = False
            
            if args.strip != None:
                if "b" in args.strip:
                    strip_all_line_breaks = True
                if args.strip.count("H") > 1:
                    if "H-end" in args.strip:
                        # In this situation, both `H` and `H-end` have been entered, and an invalid value has been provided
                        print("\nInvalid input:".upper(),"*H* and *H-end* are mutually exclusive values for *-s/--strip*.\n")
                        parser.print_help()
                        exit()
                    else:
                        # In this situation, an invalid value has been provided
                        print("\nInvalid input:".upper(),"the only acceptable values for *-s/--strip* are *b*, *H*, and *H-end*.\n")
                        parser.print_help()
                        exit()
                if "H-end" in args.strip:
                    strip_trailing_number_signs_from_headings = True
                if "H" in args.strip and "H-end" not in args.strip:
                    strip_all_heading_markup = True
                if ("b" not in args.strip and
                        "H-end" not in args.strip and
                        "H" not in args.strip):
                    # In this situation, an invalid value has been provided
                    print("\nInvalid input:".upper(),"the only acceptable values for *-s/--strip* are *b*, *H*, and *H-end*.\n")
                    parser.print_help()
                    exit()
            
            return strip_trailing_number_signs_from_headings, strip_all_heading_markup, strip_all_line_breaks
        
        cli_ctrlflw["strip_trailing_number_signs_from_headings"], cli_ctrlflw["strip_all_heading_markup"], cli_ctrlflw["strip_all_line_breaks"] = strip_choice(args, parser)

        # Code related to `link` argument begins
        
        cli_ctrlflw["make_all_links_inline_style"] = False
        cli_ctrlflw["preserve_reference_style_links"] = False
        
        if args.link != None:
            if "i" in args.link:
                cli_ctrlflw["make_all_links_inline_style"] = True
                if "p" in args.link:
                    cli_ctrlflw["preserve_reference_style_links"] = True
            else:
                # In this situation, an invalid value has been provided
                print("\nInvalid input:".upper(),"the only acceptable values for *-k/--link* are *i* or *ip*.\n")
                parser.print_help()
                exit()
        
        # Code related to `link` argument ends

        # Determining if any modifications should be made to the contents of the input file
        if (cli_ctrlflw["decrease_overall_heading_level_maximally"] == True or
                cli_ctrlflw["increase_overall_heading_level_maximally"] == True or
                cli_ctrlflw["decrease_overall_heading_level_numerically"] == True or
                cli_ctrlflw["increase_overall_heading_level_numerically"] == True or
                cli_ctrlflw["strip_trailing_number_signs_from_headings"] == True or
                cli_ctrlflw["equalize_heading_trailing_number_sign_count_with_heading_level"] == True or
                cli_ctrlflw["strip_all_heading_markup"] == True or
                cli_ctrlflw["annotate_headings"] == True):
            cli_ctrlflw["modification_to_be_made_to_heading"] = True
        if cli_ctrlflw["strip_all_line_breaks"] == True:
            cli_ctrlflw["modification_to_be_made_to_line_break"] = True
        if cli_ctrlflw["make_all_links_inline_style"] == True:
            cli_ctrlflw["modification_to_be_made_to_link"] = True
        if (cli_ctrlflw["modification_to_be_made_to_heading"] == True or
            cli_ctrlflw["modification_to_be_made_to_line_break"] == True or
            cli_ctrlflw["modification_to_be_made_to_link"] == True):
            cli_ctrlflw["modification_to_be_made"] = True

        # Input validation: at least one modification option is required in most cases.
        if cli_ctrlflw["write_in_place"] == True and cli_ctrlflw["modification_to_be_made"] == False:
                print("\nInvalid input:".upper(),"at least one modification argument is required in order to overwrite the input file.\n")
                parser.print_help()
                exit()

        cli_ctrlflw["input_filename"] = args.filename
        # Detecting command-line interface convention of indicating standard input with a single dash `-`
        if cli_ctrlflw["input_filename"].strip() == '-':
            cli_ctrlflw["input_filename"] = sys.stdin.readline()

        # Determining if the program is executing from a terminal
        if sys.stdin.isatty():
            cli_ctrlflw["executing_from_terminal"] = True
        else:
            cli_ctrlflw["executing_from_terminal"] = False

        # Stripping leading and trailing spaces
        cli_ctrlflw["input_filename"] = cli_ctrlflw["input_filename"].strip(" ")
        # Checking if a file exists
        file_exists = os.path.isfile(cli_ctrlflw["input_filename"])

        # File validation: the file must exist
        if cli_ctrlflw["executing_from_terminal"] == True:
            while file_exists == False:
                cli_ctrlflw["input_filename"] = input("The specified file does not exist. Enter a filename:")
                # Stripping leading and trailing spaces
                cli_ctrlflw["input_filename"] = cli_ctrlflw["input_filename"].strip(" ")
                # Checking if a file exists
                file_exists = os.path.isfile(cli_ctrlflw["input_filename"])
        elif cli_ctrlflw["executing_from_terminal"] == False:
            print("File does not exist. Exiting.")
            exit()
        
        return cli_ctrlflw
    
    cli_ctrlflw = assess_arguments(args, parser)
    
    return cli_ctrlflw

information_from_command_line_input = initial_input()

def markup_analysis(input_filename):
    """Analyze the contents of an input file for any markup-related information.
    
    The following things are determined for the contents of the file:
    
    - if a heading exists:
        - total heading count
        - highest heading number
        - lowest heading number
    
    The following things are determined for each line containing a heading:
    
    - beginning number sign count
    - beginning space character count (if present)
    - ending number sign count (if present)
    - ending space character count (if present)

    The `document_markup_entire` dictionary holds markup-related information in the following way:
    
    ```yaml
    break:                                               # a key containing line-break-related information
      line_numbers_containing_hard_line_breaks:          # a key containing hard-line-break-related information on the level of individual lines
        1:                                               # a key with an identifier indicating the line number of a line containing a line break
          consecutive_trailing_space_character_count: 2  # a numerical value indicating the space character count (0+) for the end of a line
      at_least_one_hard_line_break_exists: true          # an item with a boolean value indicating the presence of a hard line break
    heading:                                             # a key containing heading-related information
      line_numbers_containing_headings:                  # a key containing heading-related information on the level of individual lines
        1:                                               # a key with an identifier indicating the line number of a line containing a heading
          line_beginning_number_sign_count: 2            # a numerical value indicating the number sign count (1-6) for the beginning of a line
          heading_content: foo bar                       # a string value indicating the heading content
        2:                                               # a key with an identifier indicating the line number of a line containing a heading
          line_beginning_space_character_count: 1        # a numerical value indicating the space character count (0-3) for the beginning of a line
          line_beginning_number_sign_count: 1            # a numerical value indicating the number sign count (1-6) for the beginning of a line
          line_ending_number_sign_count: 3               # a numerical value indicating the number sign count (0+) for the end of a line
          line_ending_space_character_count: 1           # a numerical value indicating the space character count (0+) for the end of a line
          heading_content: bar baz                       # a string value indicating the heading content
      at_least_one_heading_exists: true                  # an item with a boolean value indicating the presence of a heading
      total_heading_count: 2                             # an item with a numerical value indicating the total heading count
      highest_heading_number: 2                          # an item with a numerical value indicating the highest heading number
      lowest_heading_number: 1                           # an item with a numerical value indicating the lowest heading number
    ```
    
    Using a regular expression, a line is determined to contain a heading *if the following is true*:
    
    `^(?P<leading_space_character_group>(?P<space_character_1>\s)(?P=space_character_1){0,2})?`
    : The line *optionally* starts with up to 3 space characters...
    
    `(?P<leading_heading_number_sign_group>(?P<number_sign_1>#)(?P=number_sign_1){0,5})`
    : ...followed by between 1 and 6 number signs...
    
    `($|\s)`
    : ...followed by the end of the line *or* by a space character...
    
    `(?P<heading_content>.*?)`
    : ...followed *optionally* by the heading content...
    
    `(\s(?P<trailing_number_sign_group>(?P<number_sign_2>#)(?P=number_sign_2){0,})(?P<trailing_space_character_group>(?P<space_character_2>\s)(?P=space_character_2){0,})?)?$`
    : ...followed *optionally* by a single space and a group of number signs with no upper limit, and *optionally* by a group of space characters with no upper limit.
    """
    
    # Creating a dictionary to hold markup-related information
    document_markup_entire = {}
    document_markup_entire["break"] = {}
    document_markup_entire["break"]["line_numbers_containing_hard_line_breaks"] = {}
    document_markup_entire["heading"] = {}
    document_markup_entire["heading"]["line_numbers_containing_headings"] = {}
    document_markup_entire["link"] = {}
    document_markup_entire["link"]["potential_link_label_lines"] = {}
    document_markup_entire["link"]["potential_footnote_link_label_lines"] = {}
    document_markup_entire["link"]["footnote_link_reference_definition_lines"] = {}
    document_markup_entire["link"]["inline_link_lines"] = {}
    document_markup_entire["link"]["link_reference_definition_lines"] = {}

    with open(input_filename, "r") as opened_file:
        # Assignment to hold the current line number
        current_line_number = 0
        # Assignment to indicate that there are no headings
        at_least_one_heading_exists = False
        # Assignment to indicate that there are no hard line breaks
        at_least_one_hard_line_break_exists = False
        # Assignment to indicate that there are no potential link labels
        at_least_one_potential_link_label_exists = False
        # Assignment to indicate that there are no footnote link reference definitions
        at_least_one_footnote_link_reference_definition_exists = False
        # Assignment to indicate that there are no inline links
        at_least_one_inline_link_exists = False
        # Assignment to indicate that there are no link reference definitions
        at_least_one_link_reference_definition_exists = False
        # Assignment to hold the highest and lowest heading numbers
        highest_heading_number = None
        lowest_heading_number = None
        calculation_started = False
        for current_line_string in opened_file:
            # Stripping newlines
            current_line_string = current_line_string.rstrip('\n')
            # Incrementing to keep track of the current line number
            current_line_number += 1
            # Assignment to hold the potential link label count
            potential_link_label_count = 0
            # Assignment to hold the total heading count
            total_heading_count = 0
            # Assignment to hold the total hard line break count
            total_hard_line_break_count = 0
            # Assignment to hold the total potential link label count
            total_potential_link_label_count = 0
            # Assignment to hold the total inline link count
            inline_link_count = 0

            # Determining if the current line contains any potential link labels according to the CommonMark speficication
            # Assignment to hold the current bracket character index
            current_bracket_character_index = 0
            # Assignment to hold the current right parenthesis character index
            current_right_parenthesis_character_index = 0
            # Assignment to hold the left bracket index
            # This is set to the full length of the string to prevent a false positive in a later evaluation comparing its value with the right bracket index.
            left_bracket_index = len(current_line_string)
            # Assignment to hold the right bracket index
            right_bracket_index = 0
            # Assignment to hold the right parenthesis index
            right_parenthesis_index = 0
            # Determining the positions of potential link labels.
            # This is done by examining each individual character for a left-bracket (`[`) or right-bracket (`]`). When both are found, they are compared to see if the right bracket index is greater than the left bracket index. If neither the left-bracket or right-bracket is immediately preceded by a backslash (`\`), a link label is identified, and the index numbers of the brackets are recorded in a dictionary. If multiple unclosed left-brackets are encountered before encountering a right-bracket, the left-bracket closest to the right-bracket will be used. Anything between the brackets is an unbracketed potential link label.
            for current_character in current_line_string:
                if current_character == "]" and current_bracket_character_index > 0 and current_line_string[current_bracket_character_index - 1] != "\\":
                    right_bracket_index = current_bracket_character_index
                if current_character == "[" and current_bracket_character_index == 0:
                    left_bracket_index = current_bracket_character_index
                elif current_character == "[" and current_bracket_character_index > 0 and current_line_string[current_bracket_character_index - 1] != "\\":
                    left_bracket_index = current_bracket_character_index
                # Determining if at least one character exists between the brackets, and no more than 999 characters exist between the brackets
                if (right_bracket_index - left_bracket_index) > 1 and (right_bracket_index - left_bracket_index - 1) <= 999:
                    # Determining if at least one non-space character exists between the brackets
                    at_least_one_non_space_character_exists = False
                    for current_character in current_line_string[left_bracket_index + 1:right_bracket_index - 1]:
                        if current_character != " ":
                            at_least_one_non_space_character_exists = True
                    if at_least_one_non_space_character_exists == True:
                        potential_link_label_count += 1
                        # Creating multiple dictionaries to hold potential-link-label-related information on the current line number, if none exist.
                        # This code should only be executed once per line.
                        if current_line_number not in document_markup_entire["link"]["potential_link_label_lines"]:
                            document_markup_entire["link"]["potential_link_label_lines"][current_line_number] = defaultdict(list)
                            document_markup_entire["link"]["potential_link_label_lines"][current_line_number]["potential_link_label_indexes"]
                        potential_link_label_already_stored = False
                        # Determining if the list is not empty
                        if document_markup_entire["link"]["potential_link_label_lines"][current_line_number]["potential_link_label_indexes"] == True:
                            # Determining if any list items contain the indexes for the current potential link label
                            for list_item in document_markup_entire["link"]["potential_link_label_lines"][current_line_number]["potential_link_label_indexes"]:
                                if ("left_bracket_index" in list_item and list_item["left_bracket_index"] == left_bracket_index and
                                    "right_bracket_index" in list_item and list_item["right_bracket_index"] == right_bracket_index):
                                    potential_link_label_already_stored = True
                        if potential_link_label_already_stored == False:
                            document_markup_entire["link"]["potential_link_label_lines"][current_line_number]["potential_link_label_indexes"].append({"left_bracket_index": left_bracket_index, "right_bracket_index": right_bracket_index})
                        left_bracket_index = len(current_line_string)
                        right_bracket_index = 0
                current_bracket_character_index += 1
            # Determining if any of the potential-link-label positions indicate potential footnote link labels.
            # This is done by examining the character immediately following the left bracket index of each potential link label. If it is a circumflex (`^`), this indicates a potential footnote link label.
            if current_line_number in document_markup_entire["link"]["potential_link_label_lines"]:
                # A dictionary is copied to a list for the duration of the loop in order to allow removal of dictionary items *during* the loop
                for potential_footnote_link_label_index in list(document_markup_entire["link"]["potential_link_label_lines"][current_line_number]["potential_link_label_indexes"]):
                    if current_line_string[potential_footnote_link_label_index["left_bracket_index"] + 1] == "^":
                        # Creating multiple dictionaries to hold potential-footnote-link-label-related information on the current line number, if none exist.
                        # This code should only be executed once per line.
                        if current_line_number not in document_markup_entire["link"]["potential_footnote_link_label_lines"]:
                            document_markup_entire["link"]["potential_footnote_link_label_lines"][current_line_number] = defaultdict(list)
                            document_markup_entire["link"]["potential_footnote_link_label_lines"][current_line_number]["potential_footnote_link_label_indexes"]
                        # Copying potential footnote link label indexes from list of potential-link-label positions to list of potential-footnote-link-label positions
                        document_markup_entire["link"]["potential_footnote_link_label_lines"][current_line_number]["potential_footnote_link_label_indexes"].append(potential_footnote_link_label_index)
                        # Removing copied values from list of potential-link-label positions
                        document_markup_entire["link"]["potential_link_label_lines"][current_line_number]["potential_link_label_indexes"].remove(potential_footnote_link_label_index)
            # Determining if any of the potential-footnote-link-label positions indicate footnote link reference definitions.
            # This is done by examining the character immediately following the right bracket index of each potential link label. If it is a colon (`:`), and this character is followed by one or more characters, this indicates a footnote body.
            # Warning: this code is partially reused for link reference definitions
            # Assignment to hold the post-colon character count
            post_colon_character_count = 0
            # Determining if the current line contains only one potential footnote link label
            if current_line_number in document_markup_entire["link"]["potential_footnote_link_label_lines"] and len(document_markup_entire["link"]["potential_footnote_link_label_lines"][current_line_number]["potential_footnote_link_label_indexes"]) == 1 and document_markup_entire["link"]["potential_footnote_link_label_lines"][current_line_number]["potential_footnote_link_label_indexes"][0]["left_bracket_index"] == 0:
                # Determining if the right bracket index is immediately followed by a colon
                colon_index = document_markup_entire["link"]["potential_footnote_link_label_lines"][current_line_number]["potential_footnote_link_label_indexes"][0]["right_bracket_index"] + 1
                if current_line_string[colon_index] == ":":
                    # Determining if the colon is followed by one or more characters
                    for current_character in current_line_string[colon_index + 1:]:
                        post_colon_character_count += 1
                    if post_colon_character_count != 0:
                        at_least_one_footnote_link_reference_definition_exists = True
                        footnote_body_start_index = colon_index + 1
                        footnote_body_end_index = len(current_line_string)
                        # Creating a dictionary to hold potential-footnote-link-reference-definition-related information on the current line number
                        document_markup_entire["link"]["footnote_link_reference_definition_lines"][current_line_number] = {}
                        document_markup_entire["link"]["footnote_link_reference_definition_lines"][current_line_number]["footnote_link_reference_definition_indexes"] = {}
                        # Copying footnote link reference definition index from list of potential-link-label positions to dictionary of footnote-link-reference-definition positions
                        document_markup_entire["link"]["footnote_link_reference_definition_lines"][current_line_number]["footnote_link_reference_definition_indexes"] = {"left_bracket_index": 0, "right_bracket_index": document_markup_entire["link"]["potential_footnote_link_label_lines"][current_line_number]["potential_footnote_link_label_indexes"][0]["right_bracket_index"], "footnote_body_start_index": footnote_body_start_index, "footnote_body_end_index": footnote_body_end_index}
                        # Removing now-empty sub-dictionary from dictionary of potential footnote link label lines
                        del document_markup_entire["link"]["potential_footnote_link_label_lines"][current_line_number]
            # Determining if any of the potential-link-label positions indicate inline links.
            # This is done by examining the character immediately following the right bracket index of each potential link label, so long as the right bracket index is not at the end of the line. If it is a left parenthesis (`(`), and this character is followed by zero or more characters and a right parenthesis (`)`), this indicates an inline link text followed by an inline link destination.
            # Warning: this does not follow CommonMark spec
            if current_line_number in document_markup_entire["link"]["potential_link_label_lines"]:
                # A dictionary is copied to a list for the duration of the loop in order to allow removal of dictionary items *during* the loop
                for inline_link_text_index in list(document_markup_entire["link"]["potential_link_label_lines"][current_line_number]["potential_link_label_indexes"]):
                    left_parenthesis_index = inline_link_text_index["right_bracket_index"] + 1
                    if left_parenthesis_index < len(current_line_string) and current_line_string[left_parenthesis_index] == "(":
                        current_right_parenthesis_character_index = left_parenthesis_index + 1
                        for current_character in current_line_string[left_parenthesis_index + 1:]:
                            if current_character == ")":
                                right_parenthesis_index = current_right_parenthesis_character_index
                                break
                            current_right_parenthesis_character_index += 1
                        if right_parenthesis_index > left_parenthesis_index:
                            at_least_one_inline_link_exists = True
                            inline_link_count += 1
                        if at_least_one_inline_link_exists == True:
                            # Creating multiple dictionaries to hold inline-link-related information on the current line number, if none exist.
                            # This code should only be executed once per line.
                            if current_line_number not in document_markup_entire["link"]["inline_link_lines"]:
                                document_markup_entire["link"]["inline_link_lines"][current_line_number] = defaultdict(list)
                                document_markup_entire["link"]["inline_link_lines"][current_line_number]["inline_link_indexes"]
                            # Copying inline link indexes from list of potential-link-label positions to list of inline-link positions, then removing copied values from list of potential-link-label positions.
                            document_markup_entire["link"]["inline_link_lines"][current_line_number]["inline_link_indexes"].append({"left_bracket_index": document_markup_entire["link"]["potential_link_label_lines"][current_line_number]["potential_link_label_indexes"][0]["left_bracket_index"], "right_bracket_index": document_markup_entire["link"]["potential_link_label_lines"][current_line_number]["potential_link_label_indexes"][0]["right_bracket_index"], "left_parenthesis_index": left_parenthesis_index, "right_parenthesis_index": right_parenthesis_index})
                            document_markup_entire["link"]["potential_link_label_lines"][current_line_number]["potential_link_label_indexes"].remove(inline_link_text_index)
            # Determining if any of the potential-link-label positions indicate link reference definitions.
            # This is done by examining the character immediately following the right bracket index of each potential link label. If it is a colon (`:`), and this character is followed by zero or more optional space characters and a URI, this indicates a link label followed by a link destination.
            # Warning: this does not follow CommonMark spec, and uses CommonMark terminology differently than CommonMark itself does
            # Warning: this code is partially reused for footnote link reference definitions
            # Assignment to hold the total link reference definition count
            link_reference_definition_count = 0
            # Assignment to hold the inter-colon-URI space character count
            inter_colon_uri_space_character_count = 0
            # Assignment to hold the current inter-colon-URI space character count
            current_inter_colon_uri_space_character_count = 0
            # Assignment to hold the URI start index
            uri_start_index = 0
            # Determining if the current line contains only one potential link label
            if current_line_number in document_markup_entire["link"]["potential_link_label_lines"] and len(document_markup_entire["link"]["potential_link_label_lines"][current_line_number]["potential_link_label_indexes"]) == 1 and document_markup_entire["link"]["potential_link_label_lines"][current_line_number]["potential_link_label_indexes"][0]["left_bracket_index"] == 0:
                # Determining if the right bracket index is immediately followed by a colon
                colon_index = document_markup_entire["link"]["potential_link_label_lines"][current_line_number]["potential_link_label_indexes"][0]["right_bracket_index"] + 1
                if current_line_string[colon_index] == ":":
                    # Determining if the colon is followed by zero or more optional space characters
                    for current_character in current_line_string[colon_index + 1:]:
                        if current_character != " ":
                            inter_colon_uri_space_character_count = current_inter_colon_uri_space_character_count
                            break
                        current_inter_colon_uri_space_character_count += 1
                    if inter_colon_uri_space_character_count != 0:
                        uri_start_index = colon_index + inter_colon_uri_space_character_count + 1
                    else:
                        uri_start_index = colon_index + 1
                    # Determining if the zero or more optional space characters are followed by a valid URI
                    current_uri_end_index = uri_start_index
                    # Assignment to indicate that a URI exists
                    uri_exists = True
                    for current_character in current_line_string[uri_start_index + 1:]:
                        if current_character == " ":
                            # In this situation, a non-space character is followed by a space character, and a URI does not exist
                            uri_exists = False
                            break
                        current_uri_end_index += 1
                    if uri_exists == True:
                        uri_end_index = current_uri_end_index
                        link_reference_definition_count += 1
                        at_least_one_link_reference_definition_exists = True
                        # Creating a dictionary to hold link-reference-definition-related information on the current line number
                        document_markup_entire["link"]["link_reference_definition_lines"][current_line_number] = {}
                        document_markup_entire["link"]["link_reference_definition_lines"][current_line_number]["link_reference_definition_indexes"] = {}
                        # Copying link reference definition indexes from dictionary of potential-link-label positions to dictionary of link-reference-definition positions
                        document_markup_entire["link"]["link_reference_definition_lines"][current_line_number]["link_reference_definition_indexes"] = {"left_bracket_index": 0, "right_bracket_index": document_markup_entire["link"]["potential_link_label_lines"][current_line_number]["potential_link_label_indexes"][0]["right_bracket_index"]}
                        # Removing now-empty sub-dictionary from dictionary of potential link label lines
                        del document_markup_entire["link"]["potential_link_label_lines"][current_line_number]
                        if inter_colon_uri_space_character_count != 0:
                            document_markup_entire["link"]["link_reference_definition_lines"][current_line_number]["link_reference_definition_indexes"]["inter_colon_uri_space_character_count"] = 0
                            document_markup_entire["link"]["link_reference_definition_lines"][current_line_number]["link_reference_definition_indexes"]["inter_colon_uri_space_character_count"] = inter_colon_uri_space_character_count
                        document_markup_entire["link"]["link_reference_definition_lines"][current_line_number]["link_reference_definition_indexes"]["uri_start_index"] = 0
                        document_markup_entire["link"]["link_reference_definition_lines"][current_line_number]["link_reference_definition_indexes"]["uri_end_index"] = 0
                        document_markup_entire["link"]["link_reference_definition_lines"][current_line_number]["link_reference_definition_indexes"]["uri_start_index"] = uri_start_index
                        document_markup_entire["link"]["link_reference_definition_lines"][current_line_number]["link_reference_definition_indexes"]["uri_end_index"] = uri_end_index
            # Warning: the if-constructs below this point depend on data from one another
            # Determining with a regular expression (explained in the docstring) if the current line contains a heading according to the CommonMark speficication
            current_line_string_heading_regex_match_object = re.search(r'^(?P<leading_space_character_group>(?P<space_character_1>\s)(?P=space_character_1){0,2})?(?P<leading_heading_number_sign_group>(?P<number_sign_1>#)(?P=number_sign_1){0,5})($|\s)(?P<heading_content>.*?)(\s(?P<trailing_number_sign_group>(?P<number_sign_2>#)(?P=number_sign_2){0,})(?P<trailing_space_character_group>(?P<space_character_2>\s)(?P=space_character_2){0,})?)?$', current_line_string)
            if current_line_string_heading_regex_match_object != None:
                # Assignment to indicate that at least one heading exists
                at_least_one_heading_exists = True
                total_heading_count += 1
                # Determining how many number signs exist consecutively at the *beginning* of the line
                total_consecutive_number_signs_at_beginning_of_line = len(current_line_string_heading_regex_match_object.group("leading_heading_number_sign_group"))
                # Appending this line's number to a dictionary, indicating that the current line contains a heading
                document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number] = {}
                # Appending this line's total number of consecutive number signs at the *beginning* of the line to a dictionary containing this information for all relevant lines
                document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["line_beginning_number_sign_count"] = total_consecutive_number_signs_at_beginning_of_line
                # Determining how many pre-number-sign space characters (if any) exist consecutively at the *beginning* of the line
                if current_line_string_heading_regex_match_object.group("leading_space_character_group") != None:
                    document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["line_beginning_space_character_count"] = len(current_line_string_heading_regex_match_object.group("leading_space_character_group"))
                # Determining if any heading content exists for the line
                if current_line_string_heading_regex_match_object.group("heading_content") != None:
                    document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["heading_content"] = current_line_string_heading_regex_match_object.group("heading_content")
                # Determining how many optional number signs (if any) exist consecutively at the *end* of the line
                if current_line_string_heading_regex_match_object.group("trailing_number_sign_group") != None:
                    document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["line_ending_number_sign_count"] = len(current_line_string_heading_regex_match_object.group("trailing_number_sign_group"))
                # Determining how many optional post-number-sign space characters (if any) exist consecutively at the *end* of the line
                if current_line_string_heading_regex_match_object.group("trailing_space_character_group") != None:
                    document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["line_ending_space_character_count"] = len(current_line_string_heading_regex_match_object.group("trailing_space_character_group"))
                # Determining the highest and lowest heading numbers
                if calculation_started == False:
                    highest_heading_number = total_consecutive_number_signs_at_beginning_of_line
                    lowest_heading_number = total_consecutive_number_signs_at_beginning_of_line
                    calculation_started = True
                if total_consecutive_number_signs_at_beginning_of_line > highest_heading_number and total_consecutive_number_signs_at_beginning_of_line <= 6:
                    highest_heading_number = total_consecutive_number_signs_at_beginning_of_line
                if total_consecutive_number_signs_at_beginning_of_line < lowest_heading_number:
                    lowest_heading_number = total_consecutive_number_signs_at_beginning_of_line
            # Determining with a regular expression if the current line ends with a hard line break
            current_line_string_line_break_with_two_or_more_space_characters_regex_match_object = re.search(r'\S(?P<two_or_more_consecutive_trailing_space_characters>(?P<space_character>\s)(?P=space_character){1,})$', current_line_string)
            # Checking if the regular expression was matched, and also preventing potential conflict with headings, which cannot contain line breaks
            if current_line_string_line_break_with_two_or_more_space_characters_regex_match_object != None and current_line_number not in document_markup_entire["heading"]["line_numbers_containing_headings"]:
                # Assignment to indicate that at least one hard line break exists
                at_least_one_hard_line_break_exists = True
                total_hard_line_break_count += 1
                # Appending this line's number to a dictionary, indicating that the current line contains a hard line break
                document_markup_entire["break"]["line_numbers_containing_hard_line_breaks"][current_line_number] = {}
                # Appending this line's total number of trailing space characters to a dictionary containing this information for all relevant lines
                document_markup_entire["break"]["line_numbers_containing_hard_line_breaks"][current_line_number]["consecutive_trailing_space_character_count"] = len(current_line_string_line_break_with_two_or_more_space_characters_regex_match_object.group("two_or_more_consecutive_trailing_space_characters"))
        # Removing any empty lists in “potential link label lines” dictionary
        # A dictionary is copied to a list for the duration of the loop in order to allow removal of dictionary items *during* the loop
        for potential_link_label_line in list(document_markup_entire["link"]["potential_link_label_lines"]):
            # Removing any lines that contain no potential link label indexes
            if not document_markup_entire["link"]["potential_link_label_lines"][potential_link_label_line]["potential_link_label_indexes"]:
                del document_markup_entire["link"]["potential_link_label_lines"][potential_link_label_line]
        # Resetting file object position to beginning of file
        opened_file.seek(0)
        # Resetting assignment to hold the current line number
        current_line_number = 0

        # If at least one potential link label exists and at least one link reference definition exists, extracting any existing link labels and URIs, potentially for later use in comparing potential link labels with links labels found within link reference definitions
        # Warning: this does not follow CommonMark spec, and uses CommonMark terminology differently than CommonMark itself does
        # Determining if any potential link labels exist and if any link reference definitions exist
        if bool(document_markup_entire["link"]["potential_link_label_lines"]) == True and bool(document_markup_entire["link"]["link_reference_definition_lines"]) == True:
            for current_line_string in opened_file:
                # Stripping newlines
                current_line_string = current_line_string.rstrip('\n')
                # Incrementing to keep track of the current line number
                current_line_number += 1
                # Determining if the current line has any potential link labels
                if current_line_number in document_markup_entire["link"]["potential_link_label_lines"]:
                    # Extracting normalized potential link label
                    # A dictionary is copied to a list for the duration of the loop in order to allow removal of dictionary items *during* the loop
                    for potential_link_label_indexes in list(document_markup_entire["link"]["potential_link_label_lines"][current_line_number]["potential_link_label_indexes"]):
                        potential_link_label_indexes["normalized_potential_link_label"] = current_line_string[potential_link_label_indexes["left_bracket_index"] + 1:potential_link_label_indexes["right_bracket_index"]]
                # Determining if the current line has any link reference definitions
                elif current_line_number in document_markup_entire["link"]["link_reference_definition_lines"]:
                    # Extracting normalized link label
                    document_markup_entire["link"]["link_reference_definition_lines"][current_line_number]["link_reference_definition_indexes"]["normalized_link_label"] = current_line_string[document_markup_entire["link"]["link_reference_definition_lines"][current_line_number]["link_reference_definition_indexes"]["left_bracket_index"] + 1:document_markup_entire["link"]["link_reference_definition_lines"][current_line_number]["link_reference_definition_indexes"]["right_bracket_index"]]
                    # Extracting URI
                    document_markup_entire["link"]["link_reference_definition_lines"][current_line_number]["link_reference_definition_indexes"]["uri"] = current_line_string[document_markup_entire["link"]["link_reference_definition_lines"][current_line_number]["link_reference_definition_indexes"]["uri_start_index"]:document_markup_entire["link"]["link_reference_definition_lines"][current_line_number]["link_reference_definition_indexes"]["uri_end_index"] + 1]

    # Appending information on whether or not at least one hard line break exists to a dictionary
    document_markup_entire["break"]["at_least_one_hard_line_break_exists"] = at_least_one_hard_line_break_exists
    # Appending information on whether or not at least one heading exists to a dictionary
    document_markup_entire["heading"]["at_least_one_heading_exists"] = at_least_one_heading_exists
    # Appending information on whether or not at least one footnote link reference definition exists to a dictionary
    document_markup_entire["link"]["footnote_link_reference_definition_lines"]["at_least_one_footnote_link_reference_definition_exists"] = at_least_one_footnote_link_reference_definition_exists
    # Appending information on whether or not at least one link exists to a dictionary
    if at_least_one_inline_link_exists == True or at_least_one_link_reference_definition_exists == True:
        document_markup_entire["link"]["at_least_one_link_exists"] = True
    else:
        document_markup_entire["link"]["at_least_one_link_exists"] = False
    
    # Appending additional information only if at least one heading exists
    if at_least_one_heading_exists == True:
        # Appending information on the highest and lowest heading numbers to a dictionary
        document_markup_entire["heading"]["total_heading_count"] = total_heading_count
        document_markup_entire["heading"]["highest_heading_number"] = highest_heading_number
        document_markup_entire["heading"]["lowest_heading_number"] = lowest_heading_number

    return document_markup_entire

document_markup_entire = markup_analysis(information_from_command_line_input["input_filename"])

def markup_modification(temporary_file, information_from_command_line_input, document_markup_entire):
    """Modify any existing markup in the contents of an input file.
    
    The following things can be accomplished:
    
    - decrease overall heading level maximally
    - decrease overall heading level by a numerical amount
    - increase overall heading level maximally
    - equalize heading trailing number sign count with heading level
    - increase overall heading level by a numerical amount
    - strip all heading markup
    - strip trailing number signs and any post-number-sign space characters that exist from headings
    """

    with open(information_from_command_line_input["input_filename"], "r") as opened_file:
        # Assignment to hold the current line number
        current_line_number = 0
        # Checking if any headings should be modified
        if information_from_command_line_input["modification_to_be_made_to_heading"] == True:
            # Assignments to hold default values
            number_of_heading_levels_to_decrease_in_either_case = 0
            number_of_heading_levels_to_increase_in_either_case = 0
            decrease_overall_heading_level_in_either_case = False
            increase_overall_heading_level_in_either_case = False
            # Determining how many levels to increase or decrease all headings
            if (information_from_command_line_input["decrease_overall_heading_level_maximally"] == True) or (information_from_command_line_input["decrease_overall_heading_level_numerically"] == True and document_markup_entire["heading"]["lowest_heading_number"] - information_from_command_line_input["number_of_heading_levels_to_decrease_numerically"] < 1):
                number_of_heading_levels_to_decrease_in_either_case = document_markup_entire["heading"]["lowest_heading_number"] - 1
                decrease_overall_heading_level_in_either_case = True
            elif (information_from_command_line_input["increase_overall_heading_level_maximally"] == True) or (information_from_command_line_input["increase_overall_heading_level_numerically"] == True and document_markup_entire["heading"]["highest_heading_number"] + information_from_command_line_input["number_of_heading_levels_to_increase_numerically"] > 6):
                number_of_heading_levels_to_increase_in_either_case = 6 - document_markup_entire["heading"]["highest_heading_number"]
                increase_overall_heading_level_in_either_case = True
            elif information_from_command_line_input["decrease_overall_heading_level_numerically"] == True:
                number_of_heading_levels_to_decrease_in_either_case = information_from_command_line_input["number_of_heading_levels_to_decrease_numerically"]
                decrease_overall_heading_level_in_either_case = True
            elif information_from_command_line_input["increase_overall_heading_level_numerically"] == True:
                number_of_heading_levels_to_increase_in_either_case = information_from_command_line_input["number_of_heading_levels_to_increase_numerically"]
                increase_overall_heading_level_in_either_case = True
        # Checking if any links should be modified
        if information_from_command_line_input["modification_to_be_made_to_link"] == True:
            # Warning: potential bottleneck code begins
            # Determining if any reference-style links exist
            # Determining if any shortcut reference links exist by checking if any normalized potential link labels match normalized link reference definition link labels
            # A dictionary is copied to a list for the duration of the loop in order to allow removal of dictionary items *during* the loop
            if "potential_link_label_lines" in document_markup_entire["link"]:
                for potential_link_label_line in list(document_markup_entire["link"]["potential_link_label_lines"]):
                    for potential_link_label_indexes in list(document_markup_entire["link"]["potential_link_label_lines"][potential_link_label_line]["potential_link_label_indexes"]):
                        for link_reference_definition_line in list(document_markup_entire["link"]["link_reference_definition_lines"]):
                            if potential_link_label_indexes["normalized_potential_link_label"] == document_markup_entire["link"]["link_reference_definition_lines"][link_reference_definition_line]["link_reference_definition_indexes"]["normalized_link_label"]:
                                # In this situation, a normalized potential link label matches a normalized link reference definition link label
                                # Creating a 'shortcut reference links' list within a 'reference-style link' dictionary to hold combined information on each link label and link reference definition, if it does not exist
                                # This code should only be executed once per program execution
                                if "reference_style_links" not in document_markup_entire["link"]:
                                    document_markup_entire["link"]["reference_style_links"] = dict()
                                # Data is stored as comma-separated string instead of tuple for JSON compatibility
                                document_markup_entire["link"]["reference_style_links"][str(potential_link_label_line) + "," + str(potential_link_label_indexes["left_bracket_index"]) + "," + str(potential_link_label_indexes["right_bracket_index"])] = (
                                {"normalized_link_label": potential_link_label_indexes["normalized_potential_link_label"],
                                "link_reference_definition_line": link_reference_definition_line,
                                "link_reference_definition_inter_colon_uri_space_character_count": document_markup_entire["link"]["link_reference_definition_lines"][link_reference_definition_line]["link_reference_definition_indexes"]["inter_colon_uri_space_character_count"],
                                "link_uri": document_markup_entire["link"]["link_reference_definition_lines"][link_reference_definition_line]["link_reference_definition_indexes"]["uri"]})
            # Warning: potential bottleneck code ends
            # Determining if any shortcut reference links exist
            if "reference_style_links" in document_markup_entire["link"] and bool(document_markup_entire["link"]["reference_style_links"]) == True:
                # Determining if any shortcut reference links are actually collapsed reference links
                for current_line_string in opened_file:
                    # Stripping newlines
                    current_line_string = current_line_string.rstrip('\n')
                    # Incrementing to keep track of the current line number
                    current_line_number += 1
                    # Determining if any lines contain the string `[]` that is required for a collapsed reference link, and if any shortcut reference links exist
                    if "[]" in current_line_string and bool(document_markup_entire["link"]["reference_style_links"]) == True:
                        # Iterating through all found occurrences of `[]` on the line
                        required_string_position = current_line_string.find("[]")
                        while required_string_position >= 0:
                            for link_label_position_key in document_markup_entire["link"]["reference_style_links"]:
                                # Determining if the right bracket of the link label in a shortcut reference link is followed by `[]`
                                current_link_label_position = get_link_label_position(link_label_position_key)
                                if current_link_label_position[2] + 1 == required_string_position:
                                    # In this situation, a collapsed reference link has been found
                                    document_markup_entire["link"]["reference_style_links"][link_label_position_key]["is_collapsed_reference_link"] = True
                            required_string_position = current_line_string.find("[]", required_string_position + 1)
                # Resetting file object position to beginning of file
                opened_file.seek(0)
                # Resetting assignment to hold the current line number
                current_line_number = 0
                # Warning: potential bottleneck code begins
                # Determining if any shortcut reference links are actually full reference links
                # A dictionary is copied to a list for the duration of the loop in order to allow removal of dictionary items *during* the loop
                for potential_link_label_line in list(document_markup_entire["link"]["potential_link_label_lines"]):
                    for potential_link_label_indexes in list(document_markup_entire["link"]["potential_link_label_lines"][potential_link_label_line]["potential_link_label_indexes"]):
                        for link_label_position_key in document_markup_entire["link"]["reference_style_links"]:
                            current_link_label_position = get_link_label_position(link_label_position_key)
                            # Determining if the right bracket of the potential link label is followed by the left bracket of the link label of the shortcut reference link, while also ensuring that they are on the same line.
                            if (potential_link_label_line == current_link_label_position[0] and
                                potential_link_label_indexes["right_bracket_index"] + 1 == current_link_label_position[1]):
                                # In this situation, a full reference link has been found
                                document_markup_entire["link"]["reference_style_links"][link_label_position_key]["link_text"] = potential_link_label_indexes["normalized_potential_link_label"]
                                document_markup_entire["link"]["reference_style_links"][link_label_position_key]["link_text_left_bracket_index"] = potential_link_label_indexes["left_bracket_index"]
                                document_markup_entire["link"]["reference_style_links"][link_label_position_key]["link_text_right_bracket_index"] = potential_link_label_indexes["right_bracket_index"]
                # Warning: potential bottleneck code ends
        
        def is_shortcut_reference_link(dictionary_item):
            """Determine if a dictionary item refers to a [shortcut reference link](https://spec.commonmark.org/0.29/#shortcut-reference-link).
            
            Warning: this does not follow CommonMark spec, and uses CommonMark terminology differently than CommonMark itself does.
            """
            if ("is_collapsed_reference_link" not in dictionary_item and
                "link_text" not in dictionary_item):
                is_shortcut_reference_link = True
            else:
                is_shortcut_reference_link = False
            return is_shortcut_reference_link
        
        def is_full_reference_link(dictionary_item):
            """Determine if a dictionary item refers to a [full reference link](https://spec.commonmark.org/0.29/#full-reference-link).
            """
            if "link_text" in dictionary_item:
                is_full_reference_link = True
            else:
                is_full_reference_link = False
            return is_full_reference_link

        for current_line_string in opened_file:
            # Stripping newlines
            current_line_string = current_line_string.rstrip('\n')
            # Incrementing to keep track of the current line number
            current_line_number += 1
            # Assignments to hold default values for maximizing output consistency
            remove_current_line = False
            dictionary_item_count = 0
            intermediate_adjustment_overall = 0
            document_markup_entire["link"]["temporary_dictionary"] = dict()
            # Checking if the current line contains a link to be modified
            if information_from_command_line_input["modification_to_be_made_to_link"] == True:
                if information_from_command_line_input["make_all_links_inline_style"] == True and "reference_style_links" in document_markup_entire["link"]:
                    # Any link matches on the current line are copied to a temporary dictionary that exists during modification of the current line.
                    for link_label_position_key in document_markup_entire["link"]["reference_style_links"]:
                        current_link_label_position = get_link_label_position(link_label_position_key)
                        if current_link_label_position[0] == current_line_number:
                            # Copying information on relevant reference-style links to a temporary dictionary
                            document_markup_entire["link"]["temporary_dictionary"][link_label_position_key] = document_markup_entire["link"]["reference_style_links"][link_label_position_key]
                    # Determining if the current line has any reference-style links to be made into inline-style links.
                    if bool(document_markup_entire["link"]["temporary_dictionary"]) == True:
                        for link_label_position_key in list(document_markup_entire["link"]["temporary_dictionary"]):
                            dictionary_item_count += 1
                            current_link_label_position = get_link_label_position(link_label_position_key)
                            # Changing reference-style links to inline-style links with string slices
                            # Determining if the link is a shortcut reference link
                            if is_shortcut_reference_link(document_markup_entire["link"]["temporary_dictionary"][link_label_position_key]):
                                # A complete line is created each time, in order to accommodate a situation where only one link exists
                                current_line_string = (current_line_string[:current_link_label_position[2] + 1 + intermediate_adjustment_overall] +
                                                    "(" + document_markup_entire["link"]["temporary_dictionary"][link_label_position_key]["link_uri"] + ")" +
                                                    current_line_string[current_link_label_position[2] + 1 + intermediate_adjustment_overall:])
                                intermediate_adjustment_overall += len(document_markup_entire["link"]["temporary_dictionary"][link_label_position_key]["link_uri"]) + 2
                            # Determining if the link is a full reference link
                            elif is_full_reference_link(document_markup_entire["link"]["temporary_dictionary"][link_label_position_key]):
                                current_line_string = (current_line_string[:document_markup_entire["link"]["temporary_dictionary"][link_label_position_key]["link_text_right_bracket_index"] + 1 + intermediate_adjustment_overall] +
                                                    "(" + document_markup_entire["link"]["temporary_dictionary"][link_label_position_key]["link_uri"] + ")"
                                                    + current_line_string[current_link_label_position[2] + 1 + intermediate_adjustment_overall:])
                                intermediate_adjustment_overall += (len(document_markup_entire["link"]["temporary_dictionary"][link_label_position_key]["link_uri"]) -
                                                                    (current_link_label_position[2] - current_link_label_position[1]) + 1)
                            # Determining if the link is a collapsed reference link
                            elif "is_collapsed_reference_link" in document_markup_entire["link"]["temporary_dictionary"][link_label_position_key]:
                                current_line_string = (current_line_string[:current_link_label_position[2] + 1 + intermediate_adjustment_overall] +
                                                    "(" + document_markup_entire["link"]["temporary_dictionary"][link_label_position_key]["link_uri"] + ")"
                                                    + current_line_string[current_link_label_position[2] + 3 + intermediate_adjustment_overall:])
                                intermediate_adjustment_overall += len(document_markup_entire["link"]["temporary_dictionary"][link_label_position_key]["link_uri"])
                        del document_markup_entire["link"]["temporary_dictionary"][link_label_position_key]
                    # Determining if the current line has any link reference definitions that should be removed
                    if information_from_command_line_input["preserve_reference_style_links"] == False and current_line_number in document_markup_entire["link"]["link_reference_definition_lines"]:
                        remove_current_line = True
                    
            # Checking if the current line contains a heading to be modified
            if (current_line_number in document_markup_entire["heading"]["line_numbers_containing_headings"] and
                    information_from_command_line_input["modification_to_be_made_to_heading"] == True):
                # Removing leading space characters temporarily, if any exist
                if "line_beginning_space_character_count" in document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]:
                    current_line_string = current_line_string[document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["line_beginning_space_character_count"]:]
                # Decreasing or increasing overall heading levels
                if decrease_overall_heading_level_in_either_case == True:
                    document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["line_beginning_number_sign_count"] -= number_of_heading_levels_to_decrease_in_either_case
                    # Writing a slice of a line excluding the first *N* characters, where *N* is specified in the `number_of_heading_levels_to_decrease_in_either_case` identifier
                    current_line_string = current_line_string[number_of_heading_levels_to_decrease_in_either_case:]
                elif increase_overall_heading_level_in_either_case == True:
                    document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["line_beginning_number_sign_count"] += number_of_heading_levels_to_increase_in_either_case
                    # Writing a string of number signs of *N* length, where *N* is specified in the `number_of_heading_levels_to_increase_in_either_case` identifier
                    current_line_string = ('#' * number_of_heading_levels_to_increase_in_either_case) + current_line_string
                # Reintroducing temporarily-removed leading space characters, if any exist
                if "line_beginning_space_character_count" in document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]:
                    current_line_string = (' ' * document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["line_beginning_space_character_count"]) + current_line_string
                # Removing trailing space characters temporarily, if any exist
                if "line_ending_space_character_count" in document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]:
                    current_line_string = current_line_string[:-document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["line_ending_space_character_count"]]
                # Equalizing heading trailing number sign count with heading level
                if information_from_command_line_input["equalize_heading_trailing_number_sign_count_with_heading_level"] == True and "line_ending_number_sign_count" in document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]:
                    if document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["line_ending_number_sign_count"] > document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["line_beginning_number_sign_count"]:
                        number_of_trailing_number_signs_to_remove = document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["line_ending_number_sign_count"] - document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["line_beginning_number_sign_count"]
                        # Removing a number of characters of *N* length, where *N* is specified in the `number_of_trailing_number_signs_to_remove` identifier
                        current_line_string = current_line_string[:-number_of_trailing_number_signs_to_remove]
                    elif document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["line_ending_number_sign_count"] < document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["line_beginning_number_sign_count"]:
                        number_of_trailing_number_signs_to_add = document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["line_beginning_number_sign_count"] - document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["line_ending_number_sign_count"]
                        # Writing a string of number signs of *N* length, where *N* is specified in the `number_of_trailing_number_signs_to_add` identifier
                        current_line_string = current_line_string + ('#' * number_of_trailing_number_signs_to_add)
                # Reintroducing temporarily-removed trailing space characters, if any exist
                if "line_ending_space_character_count" in document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]:
                    current_line_string = current_line_string + (' ' * document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["line_ending_space_character_count"])
                # Annotating heading by replacing a line with explanatory text followed by heading content
                if information_from_command_line_input["annotate_headings"] == True:
                    current_line_string = "Level " + str(document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["line_beginning_number_sign_count"]) + " heading. " + document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["heading_content"]
                # Stripping trailing number signs and any post-number-sign space characters that exist from headings
                if information_from_command_line_input["strip_trailing_number_signs_from_headings"] == True and "line_ending_number_sign_count" in document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]:
                    # Determining the number of trailing characters to strip. At minimum this will be a number equal to the trailing number sign count plus 1 for the required space character.
                    number_of_trailing_characters_to_strip = document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["line_ending_number_sign_count"] + 1
                    # Determining if any post-number-sign space characters exist, and adding their count to the number of trailing characters to strip if they do exist
                    if "line_ending_space_character_count" in document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]:
                        number_of_trailing_characters_to_strip += document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["line_ending_space_character_count"]
                    # Stripping a number of characters of *N* length, where *N* is specified in the `number_of_trailing_characters_to_strip` identifier
                    current_line_string = current_line_string[:-number_of_trailing_characters_to_strip]
                # Stripping all heading markup by replacing a line with the heading content
                if information_from_command_line_input["strip_all_heading_markup"] == True:
                    current_line_string = document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["heading_content"]
            # Checking if the current line contains a line break to be modified
            if (current_line_number in document_markup_entire["break"]["line_numbers_containing_hard_line_breaks"] and
                    information_from_command_line_input["modification_to_be_made_to_line_break"] == True):
                # Stripping all line breaks
                if information_from_command_line_input["strip_all_line_breaks"] == True:
                    # Determining the number of trailing characters to strip
                    number_of_trailing_characters_to_strip = document_markup_entire["break"]["line_numbers_containing_hard_line_breaks"][current_line_number]["consecutive_trailing_space_character_count"]
                    # Stripping a number of characters of *N* length, where *N* is specified in the `number_of_trailing_characters_to_strip` identifier
                    current_line_string = current_line_string[:-number_of_trailing_characters_to_strip]
            # Writing the line to a temporary file
            if remove_current_line == False:
                temporary_file.write("{}\n".format(current_line_string))

# Assignments to hold default values for maximizing output consistency
file_contents_displayed = False
modifications_have_markup_to_modify = False

# Checking if specified modifications have any markup to modify
if ((information_from_command_line_input["modification_to_be_made_to_heading"] == True and
        document_markup_entire["heading"]["at_least_one_heading_exists"] == True) or
        (information_from_command_line_input["modification_to_be_made_to_line_break"] == True and
        document_markup_entire["break"]["at_least_one_hard_line_break_exists"] == True) or
        (information_from_command_line_input["modification_to_be_made_to_link"] == True and
        document_markup_entire["link"]["at_least_one_link_exists"] == True)):
    modifications_have_markup_to_modify = True

if modifications_have_markup_to_modify == True:
    # Creating temporary file to hold intermediate modifications. The temporary file is created before calling a function so that the temporary file will still exist after exiting the function.
    with tempfile.TemporaryFile('w+') as temporary_file:
        markup_modification(temporary_file, information_from_command_line_input, document_markup_entire)
        if information_from_command_line_input["write_in_place"] == True:
            # Resetting file object position to beginning of file
            temporary_file.seek(0)
            # Resetting the current line number
            current_line_number = 0
            # Writing the file in place
            with open(information_from_command_line_input["input_filename"], "w+") as opened_file:
                for current_line_string in temporary_file:
                    opened_file.write("{}".format(current_line_string))
            # Changing assignment so that the contents of the file are not displayed after writing the file in place
            information_from_command_line_input["display_file_contents"] = False
        if information_from_command_line_input["display_file_contents"] == True:
            # Showing modifications done to temporary file before closing it
            # Resetting file object position to beginning of file
            temporary_file.seek(0)
            file_contents_displayed = True
            for current_line_string in temporary_file:
                print(current_line_string, end='')

# Displaying contents of the file
if information_from_command_line_input["display_file_contents"] == True and file_contents_displayed == False:
    with open(information_from_command_line_input["input_filename"], "r") as opened_file:
        for current_line_string in opened_file:
            print(current_line_string, end='')

def diagnostic_display(input_filename, document_markup_entire):
    "Display diagnostic information about the contents of the file."
    print(json.dumps(document_markup_entire, indent=4))
    
    ## Assignment to hold the current line number
    #current_line_number = 0
    #print("\nDiagnostic information:\n".upper())
    #if document_markup_entire["heading"]["at_least_one_heading_exists"] == True:
        ## Summarizing heading-related information.
        ## Appending information on the highest and lowest heading numbers to a dictionary
        #with open(input_filename, "r") as opened_file:
            #print("The total heading count is ",document_markup_entire["heading"]["total_heading_count"],".", sep='')
            #print("The highest heading level is ",document_markup_entire["heading"]["highest_heading_number"],".", sep='')
            #print("The lowest heading level is ",document_markup_entire["heading"]["lowest_heading_number"],".", sep='')
            #for current_line_string in opened_file:
                ## Incrementing to keep track of the current line number
                #current_line_number += 1
                #if current_line_number in document_markup_entire["heading"]["line_numbers_containing_headings"]:
                    #print("Line",current_line_number,"contains a heading.")
                    #if "line_ending_number_sign_count" in document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]:
                        #print("The beginning number sign count is ",document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["line_beginning_number_sign_count"],", and the ending number sign count is ",document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["line_ending_number_sign_count"],".", sep='')
                    #else:
                        #print("The beginning number sign count is ",document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["line_beginning_number_sign_count"],".", sep='')
                #else:
                    #print("Line",current_line_number,"does not contain a heading.")
    #elif at_least_one_heading_exists == False:
        #print("No headings were found.")

if information_from_command_line_input["diagnostic"] == True:
    diagnostic_display(information_from_command_line_input["input_filename"], document_markup_entire)


temporary_json_file_containing_information_from_command_line_input.close()
temporary_json_file_containing_document_markup_entire.close()
