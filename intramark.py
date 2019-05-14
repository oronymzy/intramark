import argparse
import os
import os.path
import sys
import tempfile

# Assignment to hold global constant
NUMBER_SIGN = '#'

# Assignments to hold default values for maximizing output consistency
modification_to_be_made = False
mkd_output_produced = False
produce_mkd_output = True

# Using the argparse module
parser = argparse.ArgumentParser(prefix_chars='-+')
parser.add_argument("filename", help="filename for input", default="None")
parser.add_argument("-d", "--diagnostic", help="produce diagnostic information on the provided input instead of output", action="store_true")
parser.add_argument("+H", dest="plus_H", help="increase heading level by a numerical amount, or *max* for maximum allowable amount", default="None")
parser.add_argument("-H", dest="minus_H", help="decrease heading level by a numerical amount, or *max* for maximum allowable amount", default="None")
parser.add_argument("-w", "--write-in-place", help="overwrite input file", action="store_true")
modification_group = parser.add_argument_group('modification arguments', 'By default, the relative hierarchical differences between headings will be preserved.')
mutually_exclusive_modification_group = modification_group.add_mutually_exclusive_group()
mutually_exclusive_modification_group.add_argument("--heading-decrease-max", help="decrease heading levels to maximum allowable amount", action="store_true")
mutually_exclusive_modification_group.add_argument("--heading-increase-max", help="increase heading levels to maximum allowable amount", action="store_true")
args = parser.parse_args()

if args.diagnostic == True:
    diagnostic = True
    produce_mkd_output = False
else:
    diagnostic = False

if args.write_in_place == True:
    write_in_place = True
else:
    write_in_place = False

if args.heading_decrease_max == True or args.minus_H == "max":
    decrease_overall_heading_level_maximally = True
else:
    decrease_overall_heading_level_maximally = False

if args.heading_increase_max == True or args.plus_H == "max":
    increase_overall_heading_level_maximally = True
else:
    increase_overall_heading_level_maximally = False

if decrease_overall_heading_level_maximally == True or increase_overall_heading_level_maximally == True:
    modification_to_be_made = True

# Input validation: at least one modification option is required in most cases.
if write_in_place == True and modification_to_be_made == False:
        print("\nInvalid input:".upper(),"at least one modification argument is required in order to overwrite the input file.\n")
        parser.print_help()
        exit()

user_input = args.filename
# Detecting command-line interface convention of indicating standard input with a single dash `-`
if user_input.strip() == '-':
    user_input = sys.stdin.readline()

# Determining if the program is executing from a terminal
if sys.stdin.isatty():
    executing_from_terminal = True
else:
    executing_from_terminal = False

# Removing leading and trailing spaces
user_input = user_input.strip(" ")
# Checking if a file exists
file_exists = os.path.isfile(user_input)

# File validation: the file must exist
if executing_from_terminal == True:
    while file_exists == False:
        user_input = input("The specified file does not exist. Enter a filename:")
        # Removing leading and trailing spaces
        user_input = user_input.strip(" ")
        # Checking if a file exists
        file_exists = os.path.isfile(user_input)
elif executing_from_terminal == False:
    print("File does not exist. Exiting.")
    exit()

# Creating an empty list, with each element holding the number sign count for the beginning of an individual line
individual_line_beginning_number_sign_count = list()
# Creating an empty list, with each element holding the number sign count for the ending of an individual line
individual_line_ending_number_sign_count = list()
# Creating an empty list, with each element indicating the presence of a heading on an individual line
individual_line_contains_heading = list()
# Creating an empty list, with each element holding the total number sign count for an individual line
individual_line_total_number_sign_count = list()

# Determining the following things for the entire file:
# - highest heading number
# - lowest heading number
# - total heading count
# - total line count
# Determining the following things for each individual line:
# - if a heading exists
with open(user_input, "r") as opened_file:
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
        current_line_string = current_line_string.strip()
        # Incrementing to keep track of the current line number
        current_line_number += 1
        # Determining if the current line contains any number signs
        if NUMBER_SIGN in current_line_string:
            # Determining how many number signs are in the current line
            total_number_signs_in_current_line_string = current_line_string.count(NUMBER_SIGN)
            individual_line_total_number_sign_count.append(total_number_signs_in_current_line_string)
            # Determining how many number signs exist consecutively at the *beginning* of the line
            total_consecutive_number_signs_at_beginning_of_line = 0
            for current_character in current_line_string:
                if current_character == NUMBER_SIGN:
                    total_consecutive_number_signs_at_beginning_of_line += 1
                else:
                    break
            individual_line_beginning_number_sign_count.append(total_consecutive_number_signs_at_beginning_of_line)
            # Determining the highest and lowest heading numbers
            if calculation_started == False:
                highest_heading_number = total_consecutive_number_signs_at_beginning_of_line
                lowest_heading_number = total_consecutive_number_signs_at_beginning_of_line
                calculation_started = True
            if total_consecutive_number_signs_at_beginning_of_line > highest_heading_number:
                highest_heading_number = total_consecutive_number_signs_at_beginning_of_line
            if total_consecutive_number_signs_at_beginning_of_line < lowest_heading_number:
                lowest_heading_number = total_consecutive_number_signs_at_beginning_of_line
            # Determining how many number signs exist consecutively at the *end* of the line
            total_consecutive_number_signs_at_end_of_line = 0
            for current_character in reversed(current_line_string):
                if current_character == NUMBER_SIGN:
                    total_consecutive_number_signs_at_end_of_line += 1
                else:
                    break
            individual_line_ending_number_sign_count.append(total_consecutive_number_signs_at_end_of_line)
            # Determining if the line contains a heading
            heading_detection_complete_for_current_line = False
            number_sign_count = 0
            while heading_detection_complete_for_current_line == False:
                number_sign_count += 1
                if current_line_string.startswith((NUMBER_SIGN * number_sign_count) + " ") and number_sign_count <= 6:
                    # Indicating that there is a heading
                    at_least_one_heading_exists = True
                    total_heading_count += 1
                    individual_line_contains_heading.append(True)
                    heading_detection_complete_for_current_line = True
                elif current_line_string.startswith(NUMBER_SIGN * number_sign_count) and len(current_line_string) == number_sign_count and number_sign_count <= 6:
                    # Detecting a heading where the line contains only 1-6 number signs. This is equivalent to the CommonMark speficication that a heading can be followed by a newline.
                    # Indicating that there is a heading
                    at_least_one_heading_exists = True
                    total_heading_count += 1
                    individual_line_contains_heading.append(True)
                    heading_detection_complete_for_current_line = True
                elif number_sign_count > 6:
                    heading_detection_complete_for_current_line = True
                    individual_line_contains_heading.append(False)
        else:
            individual_line_beginning_number_sign_count.append(None)
            individual_line_ending_number_sign_count.append(None)
            individual_line_total_number_sign_count.append(None)
            individual_line_contains_heading.append(False)
    # Resetting file object position to beginning of file
    opened_file.seek(0)

# Resetting the current line number
current_line_number = 0

# Accomplishing any of the following things:
# - decrease overall heading level maximally
# - increase overall heading level maximally
if decrease_overall_heading_level_maximally == True or increase_overall_heading_level_maximally == True:
    # Creating temporary file to hold intermediate modifications
    with tempfile.TemporaryFile('w+') as temporary_file:
        with open(user_input, "r") as opened_file:
            # Determining how many levels to increase or decrease all headings
            if decrease_overall_heading_level_maximally == True:
                number_of_heading_levels_to_decrease = lowest_heading_number - 1
            elif increase_overall_heading_level_maximally == True:
                number_of_heading_levels_to_increase = 6 - highest_heading_number
            for current_line_string in opened_file:
                # Removing newlines
                current_line_string = current_line_string.strip()
                if decrease_overall_heading_level_maximally == True and individual_line_contains_heading[current_line_number]:
                    # If a line contains a heading, write a slice of that line excluding the first *N* characters, where *N* is specified in the `number_of_heading_levels_to_decrease` identifier.
                    current_line_string = current_line_string[number_of_heading_levels_to_decrease:]
                elif increase_overall_heading_level_maximally == True and individual_line_contains_heading[current_line_number]:
                    # If a line contains a heading, write a string of number signs of *N* length, where *N* is specified in the `number_of_heading_levels_to_increase` identifier.
                    current_line_string = (NUMBER_SIGN * number_of_heading_levels_to_increase) + current_line_string
                # Writing the line to a temporary file
                temporary_file.write("{}\n".format(current_line_string))
                # Incrementing to keep track of the current line number
                current_line_number += 1
        # Writing the file in place
        if write_in_place == True:
            # Resetting file object position to beginning of file
            temporary_file.seek(0)
            # Resetting the current line number
            current_line_number = 0
            with open(user_input, "w+") as opened_file:
                for current_line_string in temporary_file:
                    opened_file.write("{}".format(current_line_string))
        elif produce_mkd_output == True:
            # Showing modifications done to temporary file before closing it
            # Resetting file object position to beginning of file
            temporary_file.seek(0)
            mkd_output_produced = True
            for current_line_string in temporary_file:
                print(current_line_string, end='')

# Displaying contents of the file
if produce_mkd_output == True and mkd_output_produced == False:
    # Resetting the current line number
    current_line_number = 0
    with open(user_input, "r") as opened_file:
        for current_line_string in opened_file:
            print(current_line_string, end='')

# Resetting the current line number
current_line_number = 0

# Summarizing heading-related information
if diagnostic == True:
    print("\nDiagnostic information:\n".upper())
    if at_least_one_heading_exists == True:
        with open(user_input, "r") as opened_file:
            print("The total heading count is ",total_heading_count,".", sep='')
            print("The highest heading level is ",highest_heading_number,".", sep='')
            print("The lowest heading level is ",lowest_heading_number,".", sep='')
            for current_line_string in opened_file:
                if individual_line_contains_heading[current_line_number]:
                    print("Line",current_line_number + 1,"contains a heading.")
                    print("Line",current_line_number + 1,"has",individual_line_total_number_sign_count[current_line_number],"total number signs", end='')
                    if individual_line_ending_number_sign_count[current_line_number]:
                        print(":",individual_line_beginning_number_sign_count[current_line_number],"at the beginning, and",individual_line_ending_number_sign_count[current_line_number],"at the end.")
                    else:
                        print(", all of which are at the beginning of the line.")
                else:
                    print("Line",current_line_number + 1,"does not contain a heading.")
                # Incrementing to keep track of the current line number
                current_line_number += 1
    elif at_least_one_heading_exists == False:
        print("No headings were found.")
