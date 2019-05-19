#!/usr/bin/python
### Note that if you have multiple IDENTICAL linklabels, the value of the last one in the file wins.
import re
import os
import subprocess
#
# Delete the temp files in /tmp (namely /tmp/2, /tmp/3, and /tmp/finalfile2) if they exist.
# Those files are from a previous run - unless they were deleted manually.
#
if os.path.isfile('/tmp/2'):
	subprocess.check_output("rm /tmp/2 ", shell=True)
if os.path.isfile('/tmp/3'):
	subprocess.check_output("rm /tmp/3 ", shell=True)
if os.path.isfile('/tmp/finalfile2'):
	subprocess.check_output("rm /tmp/finalfile2 ", shell=True)
#
inputfile = raw_input("What is the input file's name? ")
if inputfile.strip() == '':
	print "You did NOT enter a file name."
	exit()

exists = os.path.isfile(inputfile)
readable = os.access(inputfile, os.R_OK)

if exists:
	print "File EXISTS."
else:
	print "File \"%s\" does NOT exist." %inputfile
	exit()

if readable:
	print "File is READABLE."
else:
	print "File \"%s\" is NOT readable." %inputfile
	exit()

command = "wc -l " + str(inputfile) + " |awk '{print $1}'"
inputfilesize = subprocess.check_output(command, shell=True)
#print inputfilesize

if int(inputfilesize) > 0:
	print "File is not zero lines in length."
else:
	print "File \"%s\" is empty." %inputfile
	exit()

inputfilepath = inputfile
outputfilepath = '/tmp/2'
outputForDictfilepath = '/tmp/3'
outputfilepath2 = '/tmp/finalfile2'

dict = {}
outfile = open(outputfilepath,"a+") 
outfileForDict = open(outputForDictfilepath,"a+") 
with open(inputfilepath) as fp:  
	line = fp.readline()
	count = 1
	while line:
#		line = re.sub(r' +(\n|\Z)', r'\1', line) # remove spaces at end of line
		line = re.sub(r' +(\n)', r'\1', line) # remove spaces at end of line
		m00 = re.match("(^[#`]+)",line) # or m0 = re.match("(^$)",line) #find lines starting with # or `
                #print(bool(m00))
		m11 = re.match("(^$)",line) #find blank lines
                #print(bool(m11))
                m1 = re.match("(^\[[a-zA-Z0-9 ]+\]:[ ]*[a-z]+://[a-zA-Z0-9\.\/\_\-]+)",line) #find  link label definitions
                #print(bool(m1))
                m2 = re.match("(^\[\^[a-zA-Z0-9 ]+\]:[ ]*[a-z]+://[a-zA-Z0-9\.\/\_\-]+)",line) #find foot notes
                #print(bool(m2))
		####m3 = re.match('([ ]*\[*[^\[\]]+\]*[ ]*\.*)', line) # added \.* to get a potential . at the end of the line
		m3 = re.match('([ ]*\[*[^\[\]]+\]*[ ]*)', line) #find link-text-link-label-groups
                #print(bool(m3))
                if m00 or m11:
                        outfile.write(line)
			#print "HERE - M00 or M11"
                elif m1:
                        outfileForDict.write(line) # write line to a DIFFERENT file
                elif m2:
                        outfile.write(line)
			#print "HERE - M2"
		elif m3:
			elements = re.findall(r'\[*[^\[\]]+\]*\.*', line.strip('\n')) # added \.* to get a potential . at the end of the line
			elements_orig = elements
			#print elements
                        outfile.write(line)
			print "HERE - M3"
		else:
                        outfile.write(line)

		line = fp.readline()
		count += 1
		print "count is %d" %(count)
fp.close()
outfile.close()
outfileForDict.close()

outfileForDict = open(outputForDictfilepath,"a+") 
subprocess.call("sed -i 's/]: */]: /g' " + str(outputForDictfilepath) , shell=True)

dict = {}
with open(outputForDictfilepath) as fp2:  
	for line in fp2.readlines():
		linklabel,url = line.split(": ")
		dict[linklabel] = str(url)
fp2.close()
for i in dict:
	print i, dict[i]
#exit()
print "______________"

outfile2 = open(outputfilepath2,"a+") 
with open(inputfilepath) as fp:  
	line = fp.readline()
	count = 1
	while line:
		#elements = []
        	m3 = re.match('(^[^#`:/]+$)',line)
        	#print(bool(m3))
        	m4 = re.match('^$',line)
        	#print(bool(m4))
		if m3 and not m4:
			#print line
			elements = re.findall(r'\[*[^\[\]]+\]*\.*', line.strip('\n')) # added \.* to get a potential . at the end of the line
			for element in elements:
				index = elements.index(element)
				if element in dict.keys():
					print "%s " %(element)
					print element
					element = str(element) + "(" + str(dict[element].strip()) + ")"
					element = element.strip()
					elements[index] = element
					print element

			line = ''.join(elements) + "\n"
			line = re.sub(r'\)[ ]*\[[a-zA-Z0-9 _-]+\]', ')', line)
			outfile2.write(line)

		elif not m3 and not m4 and not re.match('(\[\^)',line): # the rest of lines not caught by the above (m3 and not m4) and excluding the line with the footnote.
			print "The line in ELSE is %s " %line
			line_split = line.split(":") # splitting the remaining lines in the input files - what's left are the link label definitions
			print line_split[0]
			print "THE ELEMENTS"
			print elements_orig
			print elements
			if line_split[0] not in elements_orig:
				#print "reached IT"
				outfile2.write(line)
		else:
			outfile2.write(line)
			
		line = fp.readline()
		count += 1
		print "count is %d" %(count)

#for element in elements:
#	print elements[1]

dict = {}
fp.close()

elements = []
#exit()
outfile2.close()

while True:
	response = raw_input("The output is saved in /tmp/finalfile2.\nDo you want to display the file's contents? (yes or no) ").strip()
	while response.lower() not in ("yes","ye", "y", "no", "n"):
		response = raw_input("The output is saved in /tmp/finalfile2.\nDo you want to display the file's contents? (yes or no) ").strip()
	if response.lower() == 'yes' or response.lower() == 'ye' or response.lower() == 'y':
		os.system("cat /tmp/finalfile2") # remove blank lines from the input file
		break
	elif response == 'no' or response.lower() == 'n':
		break
'''
Source:
https://stackoverflow.com/questions/30776900/python-how-to-add-a-space-string-to-the-end-of-every-line-in-a-text-conf
'''
