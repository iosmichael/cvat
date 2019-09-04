# Copyright (C) 2018 Intel Corporation
#
# SPDX-License-Identifier: MIT

format_spec = {
    "name": "GURU",
    "dumpers": [
        {
            "display_name": "{name} {format} {version}",
            "format": "JSON",
            "version": "1.0",
            "handler": "dump"
        },
    ],
    "loaders": [
        {
            "display_name": "{name} {format} {version}",
            "format": "JSON",
            "version": "1.0",
            "handler": "load"
        },
    ],
}

def dump(file_object, annotations):
    import numpy as np
    import json
    from collections import OrderedDict

    def insert_license_data(result_annotation):
        """Fill license fields in annotation by blank data
        Args:
            result_annotation: output annotation in COCO representation
        """
        result_annotation['licenses'] = []
        result_annotation['licenses'].append(OrderedDict([
            ('name', 'GURU AI RESEARCH GROUP 2019'),
            ('id', 0),
            ('url', ''),
        ]))

    def insert_categories_data(annotations, result_annotation):
        """Get labels from input annotation and fill categories field in output annotation
        Args:
            xml_root: root for xml parser
            result_annotation: output annotation in COCO representation
            labels_file: path to file with labels names.
                        If not defined, parse annotation to get labels names
        """
        def get_categories(names, sort=False):
            category_map = {}
            categories = []
            # Sort labels by its names to make the same order of ids for different annotations
            if sort:
                names.sort()
            cat_id = 0
            for name in names:
                category_map[name] = cat_id
                categories.append(OrderedDict([
                    ('id', cat_id),
                    ('name', name)
                ]))
                cat_id += 1
            return category_map, categories

        label_names = [label[1]["name"] for label in annotations.meta['task']['labels']]

        category_map, categories = get_categories(label_names, sort=True)

        result_annotation['categories'] = categories
        return category_map

    '''
    insert data format:
    - item:
       - id:
       - category:
       - points:
            [- frame_id:
             - value:]
    '''
    def dump_track(idx, track):
        track_id = idx
        track_data = OrderedDict([
            ("id", str(track_id)),
            ("label", track.label),
        ])

        if track.group:
            track_data['group_id'] = str(track.group)
        # dumper.open_track(dump_data)
        shapes_data = []
        for shape in track.shapes:
            shape_data = OrderedDict([
                ("frame", str(shape.frame)),
                ("outside", str(int(shape.outside))),
                ("occluded", str(int(shape.occluded))),
                ("keyframe", str(int(shape.keyframe))),
                ("type", shape.type)
            ])

            if shape.type == "rectangle":
                shape_data.update(OrderedDict([
                    ("xtl", "{:.2f}".format(shape.points[0])),
                    ("ytl", "{:.2f}".format(shape.points[1])),
                    ("xbr", "{:.2f}".format(shape.points[2])),
                    ("ybr", "{:.2f}".format(shape.points[3])),
                ]))
            else:
                shape_data.update(OrderedDict([
                    ("points", ';'.join(['{:.2f},{:.2f}'.format(x, y)
                        for x,y in pairwise(shape.points)]))
                ]))

            if annotations.meta["task"]["z_order"] != "False":
                shape_data["z_order"] = str(shape.z_order)
            shapes_data.append(shape_data)

        track_data['shapes'] = shapes_data
        return track_data

    counter = 0
    tracks_data = OrderedDict()
    insert_license_data(tracks_data)
    category_map = insert_categories_data(annotations, tracks_data)
    tracks_data['meta'] = annotations.meta
    tracks_data['tracks'] = []
    for track in annotations.tracks:
        tracks_data['tracks'].append(dump_track(counter, track))
        counter += 1

    file_object.write(json.dumps(tracks_data, indent=2).encode())
    file_object.flush()

def load(file_object, annotations):
    # not implemented
    pass