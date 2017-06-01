"""Compare each sample with a point cloud, and label it accordingly.

Usage:
    label.py [options]

Options:
    --template=<path>   Path to templates [default: ./data/templates/*.npy]
    --raw=<path>        Path to unclassified data [default: ./data/raw/*.npy]
    --out=<out>         Path for final results [default: ./out/labels.npy]
"""

import docopt
import glob
import numpy as np
import os
import os.path
from thirdparty.icp import icp

from math import atan
from sklearn import linear_model
from scipy.sparse.linalg import svds
from scipy.ndimage.interpolation import rotate
from sklearn.decomposition import PCA
from typing import List
from typing import Callable


def load_data(path_glob: str) -> np.array:
    """Load all point clouds."""
    P = []
    for path in sorted(glob.iglob(path_glob)):
        p = np.load(path)
        if len(p.shape) == 3:
            n = np.prod(p.shape[:2])
            p = p.reshape((n, -1))
            p = p[:,:3][np.nonzero(p)[0]]
        P.append(p)
    return P


def label(templates: np.array, samples: np.array) -> np.array:
    """Use ICP to classify all samples."""
    labels = None
    for sample in samples:
        results = [icp(sample, template, max_iterations=1) for template in templates]
        distances = [np.sum(distance) for _, _, distance in results]

        i = int(np.argmin(distances))
        T, t, _ = results[i]  # T (4x4) and t (3x1)
        label = np.hstack((distances[i], np.ravel(T), np.ravel(t)))
        labels = label if labels is None else np.vstack((labels, label))
    if labels is None:
        raise UserWarning('No samples found.')
    labels[:,1] = 1 - (labels[:,1] / np.max(labels[:,1]))
    return labels


def main():
    arguments = docopt.docopt(__doc__)

    template_path = arguments['--template']
    raw_path = arguments['--raw']
    out_path = arguments['--out']

    templates = load_data(template_path)
    samples = load_data(raw_path)

    labels = label(templates, samples)

    os.makedirs(os.path.basename(out_path), exist_ok=True)
    np.save(out_path, labels)

if __name__ == '__main__':
    main()
