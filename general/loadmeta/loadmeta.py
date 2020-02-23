import time
import sys

# Get dictionary of parameters
def loadmeta(metafile):
  metadata = {}
  with open(metafile) as f:
    for line in f:
      if line.startswith('#') or not line.strip():
        continue
      else:
        k = line.split(':')[0]
        v = line.split(':')[1].strip()
        metadata[k] = v
  return metadata
