import os
import fnmatch

def get_image_data(path_to_data):
    def get_image_key(item):
        return int(os.path.splitext(os.path.basename(item))[0])

    image_list = []
    for root, _, filenames in os.walk(path_to_data):
        for filename in fnmatch.filter(filenames, "*.jpg"):
            image_list.append(os.path.join(root, filename))

    image_list.sort(key=get_image_key)
    return image_list
