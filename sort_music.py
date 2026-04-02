#!/usr/bin/python3

from pathlib import Path
import re
import shutil
import argparse
import yaml
import glob
import os

instruments_dictionary = {
    "voice"   : {"include" : [".*voice.*",".*choir.*",".*solo.*"], "exclude" : []},
    "audio"   : {"include" : [".*audio.*",".*midi.*"], "exclude" : []},
    "flute"   : {"include" : [".*flute.*"], "exclude" : []},
    "oboe"    : {"include" : [".*oboe.*"], "exclude" : []},
    "clarinet" : {"include" : [".*clarinet.*"], "exclude" : [".*clarinet_bass.*"]},
    "clarinet_bass" : {"include" : [".*clarinet_bass.*"], "exclude" : []},
    "bassoon" : {"include" : [".*bassoon.*"], "exclude" : []},
    "horn" : {"include" : [".*horn.*"], "exclude" : []},
    "trumpet" : {"include" : [".*trumpet.*"], "exclude" : []},
    "trombone" : {"include" : [".*trombone.*"], "exclude" : []},
    "tuba" : {"include" : [".*tuba.*"], "exclude" : []},
    "timpani" : {"include" : [".*timpani.*"], "exclude" : []},
    "percussion" : {"include" : [".*percussion.*", ".*triangle.*", ".*glockenspiel.*", ".*drum_snare.*", ".*piatti.*"], "exclude" : []},
    "harp" : {"include" : [".*harp.*"], "exclude" : []},
    "piano" : {"include" : [".*piano.*", ".*rhythm.*", ".*synth.*"], "exclude" : []},
    "violin_i" : {"include" : [".*violin_i.*", ".*violin_i_ii.*", ".*violin_1.*", ".*violin_1_2.*"], "exclude" : [".*violin_ii", ".*violin_iii.*"]},
    "violin_ii" : {"include" : [".*violin_i_ii.*", ".*violin_1_2.*", ".*violin_ii.*", ".*violin_2.*"], "exclude" : [".*violin_iii.*"]},
    "violin_iii" : {"include" : [".*violin_iii.*", ".*violin_3.*"], "exclude" : []},
    "viola" : {"include" : [".*viola.*"], "exclude" : []},
    "cello" : {"include" : [".*cello.*", ".*violoncello.*"], "exclude" : []},
    "c-bass" : {"include" : [".*c-bass.*", ".*contrabass.*", ".*guitar_bass.*"], "exclude" : []}
}

class Song:

    def __init__(self, name, root_dir, extension='pdf'):
        ''' Create an object that contains the following info:
            1. Name of the song.  
                Ex: Hallelujah
            2. Directory path where the song is stored. 
                Ex: .../Dropbox/hopeOrchestra/
            3. Absolute path to that song. 
                Ex: .../Dropbox/hopeOrchestra/Hallelujah/
            4. Path to the folder when the individual parts are stored. 
                Ex: .../Dropbox/hopeOrchestra/Hallelujah/Parts/
        '''
        self.name = name
        self.extension = extension
        self.root_dir = root_dir
        # Check if the path to the song exist
        self.path_to_song = Path(root_dir).joinpath(name)
        if not self.path_to_song.exists():
            raise Exception("This path does not exist: {}".format(self.path_to_song))
        # We are expecting only two locations where the music files can be
        # stored.  It is either under the root_dir/name or root_dir/name/Parts
        # Check if root_dir/name/Parts exists, and if not, use root_dir/name
        temp = Path(self.path_to_song).joinpath("Parts")
        if not temp.exists():
            self.path_to_files = self.path_to_song
        else:
            self.path_to_files = temp

    def list_of_files(self):
        ''' Returns a list of files that are stored under the current
            path_to_files directory
        '''
        return [f.stem for f in self.path_to_files.iterdir() if f.is_file()]


    def __str__(self):
        text = '''Song Name: {0} \nRoot Directory: {1} \nPath to the Song: {2} \nPath to music files: {3}''' \
        .format(self.name, self.root_dir, self.path_to_song, self.path_to_files)
        return text

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = "Sort music PDF files")
    parser.add_argument('-f', '--forse_update', type=bool, action = "store",
                        dest = "update", required = False,
                        help = "Forse overwrite of existing PDF files")
    parser.add_argument('-i', '--directories', type=bool, action = "store",
                        dest = "create_dirs", required = False,
                        help = "Creates directories under INSTRUMENTS folder")
    parser.add_argument('-m', '--music_list', type=bool, action = "store",
                        dest = "music_list", required = False,
                        help = "Lists all music") 
    parser.add_argument('-d', '--delete_song', type=bool, action = "store",
                        dest = "delete_song", required = False,
                        help = "Delete song(s) from all INSTRUMENT folders")
    parser.add_argument('-c', '--copy_song', type=bool, action = "store",
                        dest = "copy_song", required = False,
                        help = "Copy song(s) to all INSTRUMENTs folders")

    args = parser.parse_args()

    print("force update = {}".format(args.update))

    try:
        with open('config.yml', 'r') as file:
            conf = yaml.safe_load(file)
    except Exception as e:
        print(e)
        quit()

    def create_instrument_directories(dir_path):
        ''' Creates instrument directory based on the provided root instrument
            directory path and instrument name found in instruments_dictionary
        '''
        for x in instruments_dictionary.keys():
            directory = (dir_path+x).upper()
            Path(directory).mkdir(parents=True, exist_ok=True)
    # Create sub-directories for the instruments if requested
    if (args.create_dirs):
        create_instrument_directories("./")


    def list_music_folders(dir_path):
        ''' Lists all directories found under the provided root directory
            This will be the names of all songs found under the main music folder
        '''
        p = Path(dir_path)
        directories_list = [f for f in p.iterdir() if f.is_dir()]
        for i in directories_list:
            print(i.stem)

    # List all songs in the upper directory
    if (args.music_list):
        list_music_folders("../")


    def copy_files(songObj):
        ''' Takes a Song object as an input and copies individual files (instrument 
            parts) to the destination folder under new name
            Ex: .../Dropbox/song1/Parts/violin.pdf -> .../TECHNICAL/VIOLIN/[song1]_violin.pdf
        '''
        file_list = songObj.list_of_files()
        # Iterate through the dictionary of all expected instruments
        for key, value in instruments_dictionary.items():
            # Get values in the "include" list, these are wildcards
            for var in value['include']:
                inc_regex = re.compile(var, re.IGNORECASE)
                filtered_list = [i for i in file_list if re.match(inc_regex, i)]
                # Now we need to remove excluded values from the list
                for excl_var in value['exclude']:
                    excl_regex = re.compile(excl_var, re.IGNORECASE)
                    filtered_list = [j for j in filtered_list if not re.match(excl_regex, j)]
                # Now putting everything back together
                for l in filtered_list:
                    file_path = songObj.path_to_files.joinpath(l).with_suffix('.pdf')
                    to_location = Path(conf['destination_dir']).joinpath(key.upper())
                    new_file_name = '['+songObj.name+']_'+l.lower()+'.pdf'
                    to_location = to_location.joinpath(new_file_name)
                    if not to_location.exists():
                        print(to_location)
                        shutil.copy2(file_path, to_location)
                    else:
                        print("file {} exists".format(to_location))

    def delete_songs(songObj):    
        ''' Deletes the requested song(s) from all instruments directories
            dir_path: path to the instruments directory
            songObj: list of song objects
        '''
        for x in instruments_dictionary.keys():
            # Get the path to the INSTRUMENT
            where_location = Path(conf['destination_dir']).joinpath(x.upper())
            # Wildcard for the file name to get all instances
            file_name = '*'+songObj.name+'*'
            # Now we have the list of all files contained the title in question
            files_list = glob.glob(file_name, root_dir=where_location)
            # Iterate through the list, construct the absolute path and delete the file
            for i in files_list:
                file = where_location.joinpath(i)
                if os.path.exists(file):
                    os.remove(file)
                    print("removed file: {}".format(file))
                else:
                    print("file does not exist")

    list_of_songs = []
    for x in conf['other_dir']['song']:
        list_of_songs.append(Song(x, conf['other_dir']['path']))

    for s in list_of_songs:
        if (args.copy_song):
            copy_files(s)
        elif (args.delete_song):
            delete_songs(s)
    
    
