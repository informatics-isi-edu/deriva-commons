#!/usr/bin/python

import sys
import re
import string

for line in sys.stdin:
    pattern=re.compile('([^{]*{)(.*)(}.*)')
    modpattern=re.compile('([^=]*)=("[^"]*"),? *')
    m=pattern.match(line)
    if m == None:
        print(line)
    else:
#        print("0: " + m.group(0))
        modifiers=[]
        for i in modpattern.finditer(m.group(2)):
            modifiers.append(i.group(1) + '=' + re.sub(',', '\\,', i.group(2)))
        new=m.group(1) + string.join(modifiers, ', ') + m.group(3)
        print(new)
