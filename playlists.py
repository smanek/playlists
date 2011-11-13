#!/usr/bin/env python
import os.path
import os
import sys
import optparse # I would prefer argparse, but this has to run on python 2.6
import logging
import re
from collections import defaultdict


def tryint(s):
  try:
    return int(s)
  except:
    return s

# Do a human sort - so '8 - Song Title' comes before '11 - Song Title'
def alphanum_key(s):
  return [tryint(c) for c in re.split('(\d+)', s)]


class AlbumInfo(object):
  
  def __init__(self, root):
    self.root = root
    artistAndTitle = root.rsplit('/', 1)[1].split('-')
    if len(artistAndTitle) is not 2:
      # human needs to resolve ambiguity (e.g., 'Jay-z - Vol 1 - In My Lifetime')
      print "\\nAmbiguity for album '%s'" % root
      artist = raw_input("Please enter the artist: ")
      album = raw_input("Please enter the name of the album: ")
      artistAndTitle = [artist, album]
    assert len(artistAndTitle) is 2
    self.artist = artistAndTitle[0].strip()
    self.title = artistAndTitle[1].strip()
    self._filesByExtension = defaultdict(list)

  def addFile(self, file):
    nameAndExtension = file.rsplit('.', 1)
    if len(nameAndExtension) is 2:
      self._filesByExtension[nameAndExtension[1].lower()].append(os.path.relpath(file, self.root))
    else:
      logging.debug("Ignoring %s, since it has no extension", file)

  def _removeFile(self, file):
    print "removing %s" % file
    nameAndExtension = file.rsplit('.', 1)
    if len(nameAndExtension) is 2:
      self._filesByExtension[nameAndExtension[1].lower()].remove(os.path.relpath(file, self.root))

  def getFiles(self):
    return self._filesByExtension


  def getPlaylists(self):
    return self._filesByExtension['m3u']

  def hasPlaylist(self):
    return len(self.getPlaylists()) > 0

  def deletePlaylists(self):
    for absPath in [os.path.join(self.root, p) for p in self.getPlaylists()]:
      logging.debug("Deleting existing playlist %s", absPath)
      os.unlink(absPath)
      self._removeFile(absPath)

  def generatePlaylist(self):
    assert len(self.getPlaylists()) is 0, "Playlists already exist: %s" % self.getPlaylists()
    songs = self._filesByExtension['mp3']
    if len(songs) is 0:
      logging.info("Skipping album at %s, since it has no mp3s", self.root)
      return
    else:
      self._writePlaylist(sorted(songs, key = alphanum_key))

  def _writePlaylist(self, songs):
    # TODO - update self._filesByExtension
    with open("%s/%s - %s.m3u" % (self.root, self.artist, self.title), 'w') as f:
      for song in songs:
        f.write(song + '\n')


def main(root, force):
  logging.debug("In main. root = %s, force = %s", root, force)
  if not os.path.isdir(root):
    logging.error("Can't add playlists for %s - not a directory", root)
    sys.exit(1)

  generated = 0
  for album in os.listdir(root):
    # Load the album info
    info = AlbumInfo(os.path.join(root, album))
    logging.info("Analyzing %s (artist = '%s', album = '%s')", album, info.artist, info.title)

    for traversingRoot, dirs, files in os.walk(info.root):
      for file in files:
        info.addFile(os.path.join(traversingRoot, file))
        
    if info.hasPlaylist():
      if force:
        info.deletePlaylists()
      else:
        logging.debug("Skipping %s since it already has a playlist", album)
        continue

    info.generatePlaylist()
    generated += 1

  logging.info("Generated %d playlists", generated)

if __name__ == '__main__':
  usage = "usage: %prog [options] root_dir_of_albums"
  parser = optparse.OptionParser(usage = usage)
  parser.add_option('-f', '--force', dest='force', action="store_true", default=False,
                    help = """Delete existing .m3u playlists. 
Without -f, this script doesn't touch directories with existing playlists""")
  parser.add_option('-v', '--verbose', dest='verbose', action="store_true", default=False,
                    help = "Print verbose information to stdout for debugging")
  (options, args) = parser.parse_args()

  # Setup logging
  if options.verbose:
    logLevel = logging.DEBUG
  else:
    logLevel = logging.INFO
  logging.basicConfig(level=logLevel,
                      format='%(asctime)-12s %(levelname)-8s %(message)s',
                      datefmt="%m-%d %H:%M")


  if len(args) is not 1:
    print "You must supply a root directory to process. See --help"
  else:
    main(os.path.abspath(args[0]), options.force)
  
