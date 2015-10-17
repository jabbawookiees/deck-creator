import os
import csv
import subprocess
from collections import defaultdict
from datetime import timedelta

import deck_creator.parser


def compile(first_filepath, second_filepath, audio_filepath, intersect_threshold=300):
    first_segments = deck_creator.parser.parse(first_filepath)
    second_segments = deck_creator.parser.parse(second_filepath)
    intersect_threshold = timedelta(milliseconds=int(intersect_threshold))
    graph = Graph(first_segments, second_segments, intersect_threshold)

    try:
        os.mkdir('output')
        os.mkdir(os.path.join('output', 'audio'))
    except OSError:
        pass

    csv_filepath = os.path.join('output', 'deck.csv')
    with open(csv_filepath, 'wb') as csvfile:
        writer = csv.writer(csvfile)
        total_length = len(graph.components)
        for index, component in enumerate(graph.components):
            print 'Working on %d of %d' % (index + 1, total_length)
            if len(component) <= 1:
                continue
            output_path = os.path.join('output', 'audio', '%05d.mp3' % index)
            line_one = ' '.join(segment.text for segment in component.first)
            line_two = ' '.join(segment.text for segment in component.second)
            ffmpeg_crop(audio_filepath, component.compute_start(), component.compute_end(), output_path)
            writer.writerow([line_one, line_two, output_path])


def ffmpeg_crop(audio_filepath, start, end, output_path):
    command = [
        'ffmpeg',
        '-y',
        '-loglevel', 'panic',
        '-i', audio_filepath,
        '-ss', str(start.total_seconds()),
        '-to', str(end.total_seconds()),
        output_path
    ]
    subprocess.call(command)


class Graph(object):
    def __init__(self, first_segments, second_segments, intersect_threshold):
        self.intersect_threshold = intersect_threshold
        self.first_segments = first_segments
        self.second_segments = second_segments
        self.init_edges()
        self.init_components()

    def init_edges(self):
        self.edges = {}
        for i, first in enumerate(self.first_segments):
            self.edges[i] = []
        for i, first in enumerate(self.first_segments):
            for j, second in enumerate(self.second_segments):
                if self.overlap(first, second):
                    self.edges[i].append(j)
        return self.edges

    def init_components(self):
        parents = {}
        weights = {}

        def _find(node):
            if parents.get(node) is None:
                parents[node] = node
                weights[node] = 1
                return node
            elif parents[node] != node:
                parents[node] = _find(parents[node])
                return parents[node]
            else:
                return node

        def _union(first, second):
            pfirst = _find(first)
            psecond = _find(second)
            if weights[pfirst] > weights[psecond]:
                weights[pfirst] += weights[psecond]
                parents[psecond] = pfirst
            else:
                weights[psecond] += weights[pfirst]
                parents[pfirst] = psecond

        for i, first in enumerate(self.first_segments):
            for j in self.edges[i]:
                _union((0, i), (1, j))

        self.components = []
        component_map = defaultdict(Component)
        for i, first in enumerate(self.first_segments):
            group = _find((0, i))
            component_map[group].first.append(first)
        for j, second in enumerate(self.second_segments):
            group = _find((1, j))
            component_map[group].second.append(second)

        for key, value in component_map.iteritems():
            self.components.append(value)
        self.components.sort(key=lambda c: c.compute_start())
        return self.components

    def overlap(self, first, second):
        def _inside(a, b):
            return a.start <= b.start and b.end <= a.end

        def _intersect(a, b):
            if a.start >= b.start or b.start >= a.end:
                return False
            if a.end - b.start < self.intersect_threshold:
                return False
            return True

        if _inside(first, second) or _inside(second, first):
            return True
        if _intersect(first, second) or _intersect(second, first):
            return True
        return False


class Component(object):
    def __init__(self):
        self.first = []
        self.second = []

    def compute_start(self):
        return min(map(lambda s: s.start, self.first + self.second))

    def compute_end(self):
        return max(map(lambda s: s.end, self.first + self.second))

    def add_first(self, segment):
        self.first.append(segment)
        self.first.sort(key=lambda s: s.start)

    def add_second(self, segment):
        self.second.append(segment)
        self.second.sort(key=lambda s: s.start)

    def __len__(self):
        return len(self.first) + len(self.second)


if __name__ == '__main__':
    import sys
    print sys.argv
    compile(sys.argv[1], sys.argv[2], sys.argv[3])
