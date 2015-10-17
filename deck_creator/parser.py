import ass
import ass.document


def parse(filename):
    segments = []
    if filename.endswith('.ass'):
        with open(filename, 'r') as f:
            doc = ass.parse(f)
            for event in doc.events:
                if not isinstance(event, ass.document.Dialogue):
                    continue
                if event.text.strip() == '':
                    continue
                seg = Segment(event.start, event.end, event.tags_stripped())
                segments.append(seg)
    else:
        raise Exception('Invalid file format')
    return segments


class Segment(object):
    def __init__(self, start, end, text):
        self.start = start
        self.end = end
        self.text = text
