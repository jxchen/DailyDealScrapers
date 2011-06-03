#!/usr/bin/env python

import sys
import urllib
import time
import re
from datetime import datetime

LOCATIONS_LINK = 'http://www.groupon.com/noexit/all'
MAX_PAGE_LOADS_PER_SECOND = 10
DEFAULT_FILE_NAME = 'grouponData.tsv'

def extractLocs(link):
	sock = urllib.urlopen(link)
	source = sock.read()
	locations = re.findall(r'<option value=.*</option>',source)
	sock.close()
	
	locs = [x[15:x.find('\'',16,-1)] for x in locations]
	locset = set()
	
	for loc in locs:
		colonIndex = loc.find(':')
		if colonIndex > 0:
			locset.add(loc[:colonIndex])
		else:
			locset.add(loc)
	
	return locset

def extractDealInfo(location):
	sock = urllib.urlopen('http://www.groupon.com/' + location + '/all')
	rawDealText = []
	appendFlag = False
	
	for line in sock.readlines():
		if appendFlag:
			rawDealText.append(line.strip())
			appendFlag = False
		if line.find('<div class=\'view-deal-button\'>') > 0:
			appendFlag = True
	
	sock.close()
	
	dealUrls = []
	dealTitles = []
	
	for line in rawDealText:
		dealUrls.append('http://www.groupon.com' + line[line.find('href=')+6:line.find('\' title=')])
		dealTitles.append(line[line.find('title=')+7:line.find('View This Deal')-2])
	return dealUrls,dealTitles

def extractDealData(url):
	sock = urllib.urlopen(url)
	price = None
	value = None
	numBought = None
	
	valueFlag = False
	for line in sock.readlines():
		if line.find('id="amount"') > 0:
			start = line.find('$') + 1
			end = start + line[start:].find('<')
			price = int(line[start:end].replace(',',''))
		elif line.find('<dt>Value') > 0:
			valueFlag = True
		elif valueFlag:
			start = line.find('$') + 1
			end = start + line[start:].find('<')
			value = int(line[start:end].replace(',',''))
			valueFlag = False			
		elif line.find('class="sum"') > 0:
			start = 0
			numIndex = line.find('number')
			leftIndex = line.find('left')
			if numIndex > 0:
				start = numIndex + 8
			elif leftIndex > 0:
				start = leftIndex + 6
			else:
				continue
			end = start + line[start:].find('<')
			if line[start:end]:
				numBought = int(line[start:end].replace(',',''))
			
	if not numBought:
		numBought = 0
	return price,value,numBought

def main():
	locs = extractLocs(LOCATIONS_LINK)

	outFile = None
	if len(sys.argv) > 1:
		outFile = open(sys.argv[1],'w')
	else:
		outFile = open(DEFAULT_FILE_NAME,'w')
	outFile.write(str(datetime.now()) + '\n')
	outFile.write('location\ttitle\tprice\tvalue\tnumBought\turl')
	
	for loc in locs:
		dealUrls,dealTitles = extractDealInfo(loc)
		numDeals = len(dealUrls)
	
		for i in xrange(numDeals):
			price,value,numBought = extractDealData(dealUrls[i])
			if (not price or not value):
				print 'invalid: ' + dealUrls[i]
				continue
			outData = '%s\t%s\t%d\t%d\t%d\t%s' % (loc,dealTitles[i],price,value,numBought,dealUrls[i])
			print outData
			outFile.write(outData + '\n')
			time.sleep(1.0 / MAX_PAGE_LOADS_PER_SECOND)
	
	outFile.close()

if __name__ == '__main__':
	main()
