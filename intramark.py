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
    diagnostic: true                                     # an item with a boolean value indicating if diagnostic output should be displayed
    display_file_contents: false                         # an item with a boolean value indicating if the contents of the file should be displayed
    write_in_place: false                                # an item with a boolean value indicating if the file should be overwritten
    decrease_overall_heading_level_maximally: false      # an item with a boolean value indicating if the overall heading level should be decreased maximally
    increase_overall_heading_level_maximally: false      # an item with a boolean value indicating if the overall heading level should be increased maximally
    decrease_overall_heading_level_numerically: false    # an item with a boolean value indicating if the overall heading level should be decreased by a numerical amount
    number_of_heading_levels_to_decrease_numerically: 0  # an item with a numerical value indicating the number of heading levels to decrease numerically
    increase_overall_heading_level_numerically: false    # an item with a boolean value indicating if the overall heading level should be increased by a numerical amount
    number_of_heading_levels_to_increase_numerically: 0  # an item with a numerical value indicating the number of heading levels to increase numerically
    modification_to_be_made: false                       # an item with a boolean value indicating if changes should be made to the contents of the file
    input_filename: foo.bar                              # an item with a string value indicating the filename of the file to be used for input
    executing_from_terminal: false                       # an item with a boolean value indicating if the program is executing from a terminal
    remove_trailing_number_signs_from_headings: false    # an item with a boolean value indicating if trailing number signs should be removed from headings
    ```
    """
    
    # Using the argparse module
    parser = argparse.ArgumentParser(prefix_chars='-+')
    parser.add_argument("filename", help="filename for input", default=None)
    parser.add_argument("-d", "--diagnostic", help="display diagnostic information on the provided input instead of providing output", action="store_true")
    parser.add_argument("-w", "--write-in-place", help="overwrite input file", action="store_true")
    modification_group = parser.add_argument_group('modification arguments', 'By default, the relative hierarchical differences between headings will be preserved.')
    modification_group.add_argument("+H", dest="plus_H", help="increase overall heading level by a numerical amount from 1-5, or *max* for maximum allowable amount", default=None)
    modification_group.add_argument("-H", dest="minus_H", help="decrease overall heading level by a numerical amount from 1-5, or *max* for maximum allowable amount", default=None)
    modification_group.add_argument("-r", "--remove", help="remove content, *H-end* to remove trailing number signs from headings", default=None)
    mutually_exclusive_modification_group = modification_group.add_mutually_exclusive_group()
    mutually_exclusive_modification_group.add_argument("--heading-decrease-max", help="decrease overall heading level by maximum allowable amount", action="store_true")
    mutually_exclusive_modification_group.add_argument("--heading-increase-max", help="increase overall heading level by maximum allowable amount", action="store_true")
    
    args = parser.parse_args()

    # Creating a dictionary to hold command-line-related information
    initial_input = {}

    # Assignments to hold default values for maximizing output consistency
    initial_input["modification_to_be_made"] = False
    initial_input["display_file_contents"] = True

    if args.diagnostic == True:
        initial_input["diagnostic"] = True
        initial_input["display_file_contents"] = False
    else:
        initial_input["diagnostic"] = False

    if args.write_in_place == True:
        initial_input["write_in_place"] = True
    else:
        initial_input["write_in_place"] = False

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

    if args.remove == "H-end":
        initial_input["remove_trailing_number_signs_from_headings"] = True
    elif args.remove != None:
        # In this situation, an invalid value has been provided
        print("\nInvalid input:".upper(),"the only acceptable value for *-r* is *H-end*.\n")
        parser.print_help()
        exit()
    else:
        initial_input["remove_trailing_number_signs_from_headings"] = False

    if initial_input["decrease_overall_heading_level_maximally"] == True or initial_input["increase_overall_heading_level_maximally"] == True or initial_input["decrease_overall_heading_level_numerically"] == True or initial_input["increase_overall_heading_level_numerically"] == True or initial_input["remove_trailing_number_signs_from_headings"] == True:
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

    # Removing leading and trailing spaces
    initial_input["input_filename"] = initial_input["input_filename"].strip(" ")
    # Checking if a file exists
    file_exists = os.path.isfile(initial_input["input_filename"])

    # File validation: the file must exist
    if initial_input["executing_from_terminal"] == True:
        while file_exists == False:
            initial_input["input_filename"] = input("The specified file does not exist. Enter a filename:")
            # Removing leading and trailing spaces
            initial_input["input_filename"] = initial_input["input_filename"].strip(" ")
            # Checking if a file exists
            file_exists = os.path.isfile(initial_input["input_filename"])
    elif initial_input["executing_from_terminal"] == False:
        print("File does not exist. Exiting.")
        exit()
    
    return initial_input

information_from_command_line_input = initial_input()

def heading_analysis(input_filename):
    """Analyze the contents of an input file for any heading-related information.
    
    The following things are determined for the contents of the file:
    
    - if a heading exists:
        - total heading count
        - highest heading number
        - lowest heading number
    
    The following things are determined for each line containing a heading:
    
    - beginning number sign count
    - ending number sign count (if present)

    The `document_headings_entire` dictionary holds heading-related information in the following way:
    
    ```yaml
    line_numbers_containing_headings:         # a key containing heading-related information on the level of individual lines
      1:                                      # a key with an identifier indicating the line number of a line containing a heading
        line_beginning_number_sign_count: 1   # a numerical value indicating the number sign count for the beginning of a line
        line_ending_number_sign_count: 3      # a numerical value indicating the number sign count for the ending of a line
      2:                                      # a key with an identifier indicating the line number of a line containing a heading
        line_beginning_number_sign_count: 2   # a numerical value indicating the number sign count for the beginning of a line
    at_least_one_heading_exists: true         # an item with a boolean value indicating the presence of a heading on that line
    total_heading_count: 2                    # an item with a numerical value indicating the total heading count
    highest_heading_number: 2                 # an item with a numerical value indicating the highest heading number
    lowest_heading_number: 1                  # an item with a numerical value indicating the lowest heading number
    
    Using a regular expression, a line is determined to contain a heading *if the following is true*:
    
    `^((\s)\2{0,2})?`
    : The line *optionally* starts with up to 3 space characters...
    
    `((#)\4{0,5})`
    : ...followed by between 1 and 6 number signs...
    
    `($| )`
    : ...followed by the end of the line *or* by a space character.
    ```
    """
    # Creating a dictionary to hold heading-related information
    document_headings_entire = {}
    document_headings_entire["line_numbers_containing_headings"] = {}

    with open(input_filename, "r") as opened_file:
        # Assignment to hold the current line number
        current_line_number = 0
        # Assignment to indicate that there are no headings
        at_least_one_heading_exists = False
        # Assignment to hold the highest and lowest heading numbers
        highest_heading_number = None
        lowest_heading_number = None
        # Assignment to hold the total heading count
        total_heading_count = 0
        calculation_started = False
        for current_line_string in opened_file:
            # Removing newlines
            current_line_string = current_line_string.rstrip('\n')
            # Incrementing to keep track of the current line number
            current_line_number += 1
            # Determining with a regular expression (explained in the docstring) if the current line contains a heading according to the CommonMark speficication
            if re.search(r'^((\s)\2{0,2})?((#)\4{0,5})($|\s)', current_line_string) != None:
                # Assignment to indicate that at least one heading exists
                at_least_one_heading_exists = True
                total_heading_count += 1
                # Determining how many number signs exist consecutively at the *beginning* of the line
                total_consecutive_number_signs_at_beginning_of_line = 0
                for current_character in current_line_string:
                    if current_character == '#':
                        total_consecutive_number_signs_at_beginning_of_line += 1
                    else:
                        break
                # Appending this line's total number of consecutive number signs at the *beginning* of the line to a dictionary containing this information for all relevant lines
                document_headings_entire["line_numbers_containing_headings"][current_line_number] = {}
                document_headings_entire["line_numbers_containing_headings"][current_line_number]["line_beginning_number_sign_count"] = total_consecutive_number_signs_at_beginning_of_line
                # Determining the highest and lowest heading numbers
                if calculation_started == False:
                    highest_heading_number = total_consecutive_number_signs_at_beginning_of_line
                    lowest_heading_number = total_consecutive_number_signs_at_beginning_of_line
                    calculation_started = True
                if total_consecutive_number_signs_at_beginning_of_line > highest_heading_number and total_consecutive_number_signs_at_beginning_of_line <= 6:
                    highest_heading_number = total_consecutive_number_signs_at_beginning_of_line
                if total_consecutive_number_signs_at_beginning_of_line < lowest_heading_number:
                    lowest_heading_number = total_consecutive_number_signs_at_beginning_of_line
                # Determining how many number signs exist consecutively at the *end* of the line
                total_consecutive_number_signs_at_end_of_line = 0
                for current_character in reversed(current_line_string):
                    if current_character == '#':
                        total_consecutive_number_signs_at_end_of_line += 1
                    else:
                        break
                # Appending this line's total number of consecutive number signs at the *end* of the line to a dictionary containing this information for all relevant lines
                if total_consecutive_number_signs_at_end_of_line > 0:
                    document_headings_entire["line_numbers_containing_headings"][current_line_number]["line_ending_number_sign_count"] = total_consecutive_number_signs_at_end_of_line
        # Resetting file object position to beginning of file
        opened_file.seek(0)
    
    # Appending information on whether or not at least one heading exists to a dictionary
    document_headings_entire["at_least_one_heading_exists"] = at_least_one_heading_exists
    
    # Appending additional information only if at least one heading exists
    if at_least_one_heading_exists == True:
        # Appending information on the highest and lowest heading numbers to a dictionary
        document_headings_entire["total_heading_count"] = total_heading_count
        document_headings_entire["highest_heading_number"] = highest_heading_number
        document_headings_entire["lowest_heading_number"] = lowest_heading_number

    return document_headings_entire

document_headings_entire = heading_analysis(information_from_command_line_input["input_filename"])

def heading_modification(temporary_file, information_from_command_line_input, document_headings_entire):
    """Modify any existing headings in the contents of an input file.
    
    The following things can be accomplished:
    
    - decrease overall heading level maximally
    - decrease overall heading level by a numerical amount
    - increase overall heading level maximally
    - increase overall heading level by a numerical amount
    """
    
    # Decreasing or increasing overall heading levels
    if information_from_command_line_input["decrease_overall_heading_level_maximally"] == True or information_from_command_line_input["increase_overall_heading_level_maximally"] == True or information_from_command_line_input["decrease_overall_heading_level_numerically"] == True or information_from_command_line_input["increase_overall_heading_level_numerically"] == True:
        with open(information_from_command_line_input["input_filename"], "r") as opened_file:
            # Assignment to hold the current line number
            current_line_number = 0
            # Assignments to hold default values
            number_of_heading_levels_to_decrease_in_either_case = 0
            number_of_heading_levels_to_increase_in_either_case = 0
            decrease_overall_heading_level_in_either_case = False
            increase_overall_heading_level_in_either_case = False
            # Determining how many levels to increase or decrease all headings
            if (information_from_command_line_input["decrease_overall_heading_level_maximally"] == True) or (information_from_command_line_input["decrease_overall_heading_level_numerically"] == True and document_headings_entire["lowest_heading_number"] - information_from_command_line_input["number_of_heading_levels_to_decrease_numerically"] < 1):
                number_of_heading_levels_to_decrease_in_either_case = document_headings_entire["lowest_heading_number"] - 1
                decrease_overall_heading_level_in_either_case = True
            elif (information_from_command_line_input["increase_overall_heading_level_maximally"] == True) or (information_from_command_line_input["increase_overall_heading_level_numerically"] == True and document_headings_entire["highest_heading_number"] + information_from_command_line_input["number_of_heading_levels_to_increase_numerically"] > 6):
                number_of_heading_levels_to_increase_in_either_case = 6 - document_headings_entire["highest_heading_number"]
                increase_overall_heading_level_in_either_case = True
            elif information_from_command_line_input["decrease_overall_heading_level_numerically"] == True:
                number_of_heading_levels_to_decrease_in_either_case = information_from_command_line_input["number_of_heading_levels_to_decrease_numerically"]
                decrease_overall_heading_level_in_either_case = True
            elif information_from_command_line_input["increase_overall_heading_level_numerically"] == True:
                number_of_heading_levels_to_increase_in_either_case = information_from_command_line_input["number_of_heading_levels_to_increase_numerically"]
                increase_overall_heading_level_in_either_case = True
            for current_line_string in opened_file:
                # Removing newlines
                current_line_string = current_line_string.rstrip('\n')
                # Incrementing to keep track of the current line number
                current_line_number += 1
                if decrease_overall_heading_level_in_either_case == True and (current_line_number in document_headings_entire["line_numbers_containing_headings"]):
                    # If a line contains a heading, write a slice of that line excluding the first *N* characters, where *N* is specified in the `number_of_heading_levels_to_decrease_in_either_case` identifier.
                    current_line_string = current_line_string[number_of_heading_levels_to_decrease_in_either_case:]
                elif increase_overall_heading_level_in_either_case == True and (current_line_number in document_headings_entire["line_numbers_containing_headings"]):
                    # If a line contains a heading, write a string of number signs of *N* length, where *N* is specified in the `number_of_heading_levels_to_increase_in_either_case` identifier.
                    current_line_string = ('#' * number_of_heading_levels_to_increase_in_either_case) + current_line_string
                # Writing the line to a temporary file
                temporary_file.write("{}\n".format(current_line_string))

# Assignments to hold default values for maximizing output consistency
file_contents_displayed = False

if document_headings_entire["at_least_one_heading_exists"] == True and information_from_command_line_input["modification_to_be_made"] == True:
    # Creating temporary file to hold intermediate modifications. The temporary file is created before calling a function so that the temporary file will still exist after exiting the function.
    with tempfile.TemporaryFile('w+') as temporary_file:
        heading_modification(temporary_file, information_from_command_line_input, document_headings_entire)
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

def diagnostic_display(input_filename, document_headings_entire):
    "Display diagnostic information about the contents of the file."
    # Assignment to hold the current line number
    current_line_number = 0
    print("\nDiagnostic information:\n".upper())
    if document_headings_entire["at_least_one_heading_exists"] == True:
        # Summarizing heading-related information.
        # Appending information on the highest and lowest heading numbers to a dictionary
        with open(input_filename, "r") as opened_file:
            print("The total heading count is ",document_headings_entire["total_heading_count"],".", sep='')
            print("The highest heading level is ",document_headings_entire["highest_heading_number"],".", sep='')
            print("The lowest heading level is ",document_headings_entire["lowest_heading_number"],".", sep='')
            for current_line_string in opened_file:
                # Incrementing to keep track of the current line number
                current_line_number += 1
                if current_line_number in document_headings_entire["line_numbers_containing_headings"]:
                    print("Line",current_line_number,"contains a heading.")
                    if "line_ending_number_sign_count" in document_headings_entire["line_numbers_containing_headings"][current_line_number]:
                        print("The beginning number sign count is ",document_headings_entire["line_numbers_containing_headings"][current_line_number]["line_beginning_number_sign_count"],", and the ending number sign count is ",document_headings_entire["line_numbers_containing_headings"][current_line_number]["line_ending_number_sign_count"],".", sep='')
                    else:
                        print("The beginning number sign count is ",document_headings_entire["line_numbers_containing_headings"][current_line_number]["line_beginning_number_sign_count"],".", sep='')
                else:
                    print("Line",current_line_number,"does not contain a heading.")
    elif at_least_one_heading_exists == False:
        print("No headings were found.")

if information_from_command_line_input["diagnostic"] == True:
    diagnostic_display(information_from_command_line_input["input_filename"], document_headings_entire)
