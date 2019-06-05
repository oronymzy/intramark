#!/usr/bin/python3
import argparse
import os
import os.path
import re
import sys
import tempfile

def initial_input():
    """Get user input in the form of command line arguments, storing provided information in a dictionary.
    
    The `initial_input` dictionary holds command-line-related information in the following way:
    
    ```yaml
    diagnostic: true                                                       # an item with a boolean value indicating if diagnostic output should be displayed
    display_file_contents: false                                           # an item with a boolean value indicating if the contents of the file should be displayed
    write_in_place: false                                                  # an item with a boolean value indicating if the file should be overwritten
    decrease_overall_heading_level_maximally: false                        # an item with a boolean value indicating if the overall heading level should be decreased maximally
    increase_overall_heading_level_maximally: false                        # an item with a boolean value indicating if the overall heading level should be increased maximally
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
    annotate_headings: false                                               # an item with a boolean value indicating if explanatory text about a heading should be displayed instead of the heading itself
    strip_all_line_breaks: false                                           # an item with a boolean value indicating if all line break markup text should be stripped
    modification_to_be_made_to_heading: false                              # an item with a boolean value indicating if changes should be made to a heading
    modification_to_be_made_to_line_break: false                           # an item with a boolean value indicating if changes should be made to a line break
    ```
    """
    
    # Using the argparse module
    parser = argparse.ArgumentParser(prefix_chars='-+=')
    parser.add_argument("filename", help="filename for input", default=None)
    parser.add_argument("-d", "--diagnostic", help="display diagnostic information on the provided input instead of providing output", action="store_true")
    parser.add_argument("-w", "--write-in-place", help="overwrite input file", action="store_true")
    modification_group = parser.add_argument_group('modification arguments', 'By default, the relative hierarchical differences between headings will be preserved.')
    modification_group.add_argument("-A", "--annotate", help="display explanatory text about markup instead of displaying the markup itself, *H* to affect headings", default=None)
    modification_group.add_argument("+H", dest="plus_H", help="increase overall heading level by a numerical amount from 1-5, or *max* for maximum allowable amount", default=None)
    modification_group.add_argument("-H", dest="minus_H", help="decrease overall heading level by a numerical amount from 1-5, or *max* for maximum allowable amount", default=None)
    modification_group.add_argument("=H", dest="equals_H", help="equalize heading trailing number sign count with heading level", action="store_true")
    modification_group.add_argument("-s", "--strip", help="strip away markup text, *b* to strip line breaks, *H* to strip all heading markup text, or *H-end* to strip only trailing number signs and spaces from headings", default=None)
    mutually_exclusive_modification_group = modification_group.add_mutually_exclusive_group()
    mutually_exclusive_modification_group.add_argument("--heading-decrease-max", help="decrease overall heading level by maximum allowable amount", action="store_true")
    mutually_exclusive_modification_group.add_argument("--heading-increase-max", help="increase overall heading level by maximum allowable amount", action="store_true")
    
    args = parser.parse_args()

    # Creating a dictionary to hold command-line-related information
    initial_input = {}

    # Assignments to hold default values for maximizing output consistency
    initial_input["modification_to_be_made"] = False
    initial_input["modification_to_be_made_to_heading"] = False
    initial_input["modification_to_be_made_to_line_break"] = False
    initial_input["display_file_contents"] = True
    initial_input["annotate_headings"] = False

    if args.diagnostic == True:
        initial_input["diagnostic"] = True
        initial_input["display_file_contents"] = False
    else:
        initial_input["diagnostic"] = False

    if args.write_in_place == True:
        initial_input["write_in_place"] = True
    else:
        initial_input["write_in_place"] = False

    if args.annotate == "H":
        initial_input["annotate_headings"] = True
    elif args.annotate != None:
        # In this situation, an invalid value has been provided
        print("\nInvalid input:".upper(),"the only acceptable value for *-A/--annotate* is *H*.\n")
        parser.print_help()
        exit()

    # Code related to `plus_H` argument begins
    
    if args.heading_increase_max == True or args.plus_H == "max":
        initial_input["increase_overall_heading_level_maximally"] = True
    else:
        initial_input["increase_overall_heading_level_maximally"] = False

    # Determining if `plus_H` has a string that should be converted to an integer value
    if args.plus_H != None and args.plus_H != "max":
        if int(args.plus_H) >= 1 and int(args.plus_H) <= 5:
            initial_input["increase_overall_heading_level_numerically"] = True
            initial_input["number_of_heading_levels_to_increase_numerically"] = int(args.plus_H)
        else:
            print("\nInvalid input:".upper(),"acceptable values for *+H* are *max* or *1-5*.\n")
            parser.print_help()
            exit()
    else:
        initial_input["increase_overall_heading_level_numerically"] = False
    
    # Code related to `plus_H` argument ends

    # Code related to `minus_H` argument begins

    if args.heading_decrease_max == True or args.minus_H == "max":
        initial_input["decrease_overall_heading_level_maximally"] = True
    else:
        initial_input["decrease_overall_heading_level_maximally"] = False

    # Determining if `minus_H` has a string that should be converted to an integer value
    if args.minus_H != None and args.minus_H != "max":
        if int(args.minus_H) >= 1 and int(args.minus_H) <= 5:
            initial_input["decrease_overall_heading_level_numerically"] = True
            initial_input["number_of_heading_levels_to_decrease_numerically"] = int(args.minus_H)
        else:
            print("\nInvalid input:".upper(),"acceptable values for *-H* are *max* or *1-5*.\n")
            parser.print_help()
            exit()
    else:
        initial_input["decrease_overall_heading_level_numerically"] = False

    # Code related to `minus_H` argument ends

    if args.equals_H == True:
        initial_input["equalize_heading_trailing_number_sign_count_with_heading_level"] = True
    else:
        initial_input["equalize_heading_trailing_number_sign_count_with_heading_level"] = False
    
    # Code related to `strip` argument begins
    
    initial_input["strip_trailing_number_signs_from_headings"] = False
    initial_input["strip_all_heading_markup"] = False
    initial_input["strip_all_line_breaks"] = False
    
    if args.strip != None:
        if "b" in args.strip:
            initial_input["strip_all_line_breaks"] = True
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
            initial_input["strip_trailing_number_signs_from_headings"] = True
        if "H" in args.strip and "H-end" not in args.strip:
            initial_input["strip_all_heading_markup"] = True
        if ("b" not in args.strip and
                "H-end" not in args.strip and
                "H" not in args.strip):
            # In this situation, an invalid value has been provided
            print("\nInvalid input:".upper(),"the only acceptable values for *-s/--strip* are *b*, *H*, and *H-end*.\n")
            parser.print_help()
            exit()
    
    # Code related to `strip` argument ends

    # Determining if any modifications should be made to the contents of the input file
    if (initial_input["decrease_overall_heading_level_maximally"] == True or
            initial_input["increase_overall_heading_level_maximally"] == True or
            initial_input["decrease_overall_heading_level_numerically"] == True or
            initial_input["increase_overall_heading_level_numerically"] == True or
            initial_input["strip_trailing_number_signs_from_headings"] == True or
            initial_input["equalize_heading_trailing_number_sign_count_with_heading_level"] == True or
            initial_input["strip_all_heading_markup"] == True or
            initial_input["annotate_headings"] == True):
        initial_input["modification_to_be_made_to_heading"] = True
    if initial_input["strip_all_line_breaks"] == True:
        initial_input["modification_to_be_made_to_line_break"] = True
    if (initial_input["modification_to_be_made_to_heading"] == True or
        initial_input["modification_to_be_made_to_line_break"] == True):
        initial_input["modification_to_be_made"] = True

    # Input validation: at least one modification option is required in most cases.
    if initial_input["write_in_place"] == True and initial_input["modification_to_be_made"] == False:
            print("\nInvalid input:".upper(),"at least one modification argument is required in order to overwrite the input file.\n")
            parser.print_help()
            exit()

    initial_input["input_filename"] = args.filename
    # Detecting command-line interface convention of indicating standard input with a single dash `-`
    if initial_input["input_filename"].strip() == '-':
        initial_input["input_filename"] = sys.stdin.readline()

    # Determining if the program is executing from a terminal
    if sys.stdin.isatty():
        initial_input["executing_from_terminal"] = True
    else:
        initial_input["executing_from_terminal"] = False

    # Stripping leading and trailing spaces
    initial_input["input_filename"] = initial_input["input_filename"].strip(" ")
    # Checking if a file exists
    file_exists = os.path.isfile(initial_input["input_filename"])

    # File validation: the file must exist
    if initial_input["executing_from_terminal"] == True:
        while file_exists == False:
            initial_input["input_filename"] = input("The specified file does not exist. Enter a filename:")
            # Stripping leading and trailing spaces
            initial_input["input_filename"] = initial_input["input_filename"].strip(" ")
            # Checking if a file exists
            file_exists = os.path.isfile(initial_input["input_filename"])
    elif initial_input["executing_from_terminal"] == False:
        print("File does not exist. Exiting.")
        exit()
    
    return initial_input

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

    with open(input_filename, "r") as opened_file:
        # Assignment to hold the current line number
        current_line_number = 0
        # Assignment to indicate that there are no headings
        at_least_one_heading_exists = False
        # Assignment to indicate that there are no hard line breaks
        at_least_one_hard_line_break_exists = False
        # Assignment to hold the highest and lowest heading numbers
        highest_heading_number = None
        lowest_heading_number = None
        # Assignment to hold the total heading count
        total_heading_count = 0
        # Assignment to hold the total hard line break count
        total_hard_line_break_count = 0
        calculation_started = False
        for current_line_string in opened_file:
            # Stripping newlines
            current_line_string = current_line_string.rstrip('\n')
            # Incrementing to keep track of the current line number
            current_line_number += 1
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
        # Resetting file object position to beginning of file
        opened_file.seek(0)
    
    # Appending information on whether or not at least one hard line break exists to a dictionary
    document_markup_entire["break"]["at_least_one_hard_line_break_exists"] = at_least_one_hard_line_break_exists
    # Appending information on whether or not at least one heading exists to a dictionary
    document_markup_entire["heading"]["at_least_one_heading_exists"] = at_least_one_heading_exists
    
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
        for current_line_string in opened_file:
            # Stripping newlines
            current_line_string = current_line_string.rstrip('\n')
            # Incrementing to keep track of the current line number
            current_line_number += 1
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
            temporary_file.write("{}\n".format(current_line_string))

# Assignments to hold default values for maximizing output consistency
file_contents_displayed = False
modifications_have_markup_to_modify = False

# Checking if specified modifications have any markup to modify
if ((information_from_command_line_input["modification_to_be_made_to_heading"] == True and
        document_markup_entire["heading"]["at_least_one_heading_exists"] == True) or
        (information_from_command_line_input["modification_to_be_made_to_line_break"] == True and
        document_markup_entire["break"]["at_least_one_hard_line_break_exists"] == True)):
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
    # Assignment to hold the current line number
    current_line_number = 0
    print("\nDiagnostic information:\n".upper())
    if document_markup_entire["heading"]["at_least_one_heading_exists"] == True:
        # Summarizing heading-related information.
        # Appending information on the highest and lowest heading numbers to a dictionary
        with open(input_filename, "r") as opened_file:
            print("The total heading count is ",document_markup_entire["heading"]["total_heading_count"],".", sep='')
            print("The highest heading level is ",document_markup_entire["heading"]["highest_heading_number"],".", sep='')
            print("The lowest heading level is ",document_markup_entire["heading"]["lowest_heading_number"],".", sep='')
            for current_line_string in opened_file:
                # Incrementing to keep track of the current line number
                current_line_number += 1
                if current_line_number in document_markup_entire["heading"]["line_numbers_containing_headings"]:
                    print("Line",current_line_number,"contains a heading.")
                    if "line_ending_number_sign_count" in document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]:
                        print("The beginning number sign count is ",document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["line_beginning_number_sign_count"],", and the ending number sign count is ",document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["line_ending_number_sign_count"],".", sep='')
                    else:
                        print("The beginning number sign count is ",document_markup_entire["heading"]["line_numbers_containing_headings"][current_line_number]["line_beginning_number_sign_count"],".", sep='')
                else:
                    print("Line",current_line_number,"does not contain a heading.")
    elif at_least_one_heading_exists == False:
        print("No headings were found.")

if information_from_command_line_input["diagnostic"] == True:
    diagnostic_display(information_from_command_line_input["input_filename"], document_markup_entire)
