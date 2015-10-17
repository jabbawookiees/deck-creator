import ass
import ass.document


def parse(filename):
    segments = []
    if filename.endswith('.ass'):
        with open(filename, 'r') as f:
            doc = ass.parse(f)
            for event in doc.events:
                if ignore_ass_event(event):
                    continue
                seg = Segment(event.start, event.end, event.tags_stripped())
                segments.append(seg)
    else:
        raise Exception('Invalid file format')
    return segments


def ignore_ass_event(event):
    banned_tags = ['pos']
    if not isinstance(event, ass.document.Dialogue):
        return True
    if event.tags_stripped().strip() == '':
        return True
    for part in event.parse_parts():
        if isinstance(part, ass.document.Tag) and part.name in banned_tags:
            return True
        elif isinstance(part, ass.document.Tag) and '\pos(' in part.name:
            return True
    return False


class Segment(object):
    def __init__(self, start, end, text):
        self.start = start
        self.end = end
        self.text = text
