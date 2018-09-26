import xml.etree.ElementTree as ET
import urllib2
import eyed3
import sys

eyed3.log.setLevel("ERROR")

BPM = 'AverageBpm'
PATH = 'Location'
PATH_PREFIX = 'file://localhost'

def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text

'''
Some heuristics for tagging. 
Tag if old_bpm is 0, if the difference in bpm > 3 
and the ratio of bpms is > 0.05 away from the nearest integer
'''
def should_tag(old_bpm, new_bpm):
    if abs(old_bpm-new_bpm) < 0.001:
        return False

    if old_bpm == 0:
        return True

    bpm_ratio = old_bpm/new_bpm if old_bpm > new_bpm else new_bpm/old_bpm
    if abs(old_bpm-new_bpm) > 3 and abs(bpm_ratio-round(bpm_ratio) > 0.05):
        return True
    return False


tree = ET.parse('RekordboxExport.xml')
root = tree.getroot()
tracks = [track for track in root.iter('TRACK')]

retag_count = 0
for track in tracks:
    attributes = track.attrib
    if PATH in attributes and BPM in attributes:
        rb_bpm = float(attributes[BPM])
        if rb_bpm < 0.001:
            print ("No BPM from RekordBox for", attributes['Name'])
            continue

        path = urllib2.unquote(attributes[PATH].encode('utf8'))
        path = remove_prefix(path, PATH_PREFIX)
        try:
            audio_file = eyed3.load(path)
            existing_bpm = audio_file.tag.bpm
            if should_tag(existing_bpm, rb_bpm):
                retag_count = retag_count + 1
                print (retag_count, attributes['Name'], rb_bpm, existing_bpm)
                audio_file.tag.bpm = rb_bpm
                audio_file.tag.save()
        except IOError as e: # Can't find the file
            sys.exc_clear() 
        except UnicodeDecodeError as e: # Unicode in the song title, need to fix this
            sys.exc_clear()


print ("Retagged %d songs" % retag_count)
