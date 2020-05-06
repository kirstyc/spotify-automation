import json
from utils import SpotifyUtils

class Playlist():

    def __init__(self, name, desc = '', public = False):
        self.name = name
        self.desc = desc
        self.public = public
        self.spotify = SpotifyUtils()
        self.playlistId = self.getId()

    def getId(self):
        names = self.spotify.getPlaylistNames()
        if self.name in names:
            playlistId = self.spotify.getPlaylistIdFromName(self.name)
            print(f"got playlist id for {self.name}")
        else:
            playlistId = self.create()
            print(f"created playlist id for {self.name}")


        return playlistId 

    def create(self):
        playlistId = self.spotify.createPlaylist(self.name, self.desc, self.public)
        return playlistId

    def missingUris(self, newUris, playlistUris):
        missingUris = []
        for newUri in newUris:
            if newUri not in playlistUris:
                missingUris.append(newUri)
        return missingUris

class PlaylistManager():
    def __init__(self, playId):
        self.id = playId
        self.playlist = self.getPlaylist()
    
    def getPlaylist(self):
        with open('playlists.json') as f:
            data = json.load(f)

        for item in data:
            if item['id'] == self.id:
                data = item
                break

        try:
            playlistType = data['type']
        except:
            raise ValueError(f'Could not find playlist id {self.id} in file')

        playlistClass = self.getPlaylistClass(playlistType)

        # default params 
        playlistName = data['name']
        playlistDesc = data['desc']
        playlistData = data['data']

        # get playlist object 
        playlist = playlistClass(playlistData, playlistName, playlistDesc)
        return playlist

    def getPlaylistClass(self, playlistType):
        types = {
            'artist mix':ArtistMix
        }            
        
        playlistClass = types[playlistType]

        return playlistClass

    def update(self):
        self.playlist.update()


class RecentPlaylist(Playlist):
    
    def __init__(self):
        self.name = 'Recents'
        self.desc = 'Recently added music'
        self.numSongs = 20
        super().__init__(self.name, self.desc)

    def update(self):
        
        # get latest tracks
        print(f"for {self.name} Playlist: id={self.playlistId}")
        latestUris = self.spotify.getLatestTrackUris(self.numSongs)
        print(f"got {self.numSongs} latest saved tracks")

        # check which tracks are new to playlist 
        playlistUris = self.spotify.getPlaylistUris(self.playlistId)
        print(f"got current tracks from {self.name}")
        missingUris = self.missingUris(latestUris, playlistUris)
        print(f"{len(missingUris)} new tracks to add")

        # remove old songs
        numRemove = abs(self.numSongs - len(playlistUris) - len(missingUris))
        if numRemove > 0:
            datesAddedDict = self.spotify.getPlaylistAddDates(self.playlistId)
            datesAdded = list(datesAddedDict.keys()).sort()
            oldDates = datesAdded[:numRemove]
            removeUris = [datesAddedDict[date] for date in oldDates]
            self.spotify.removeSongs(self.playlistId, removeUris)
            print(f"{numRemove} old songs removed")

        # add new songs 
        self.spotify.addSongs(self.playlistId, missingUris)
        print("added new tracks")


class ArtistMix(Playlist):
    
    def __init__(self, data, playlistName, desc = "", public = False):
        super().__init__(playlistName, desc, public)
        self.artists = self.unpackData(data)
        self.artistUris = None

    def unpackData(self, data):
        return data['artists']

    def update(self):

        # get artist uris 
        self.artistUris = self.spotify.getArtistUris(self.artists)
        print("got artist uris")

        # get artist songs from library 
        artistSongUris = self.getArtistSongs()
        print("got song uris")
        # get playlist track uris 
        playlistUris = self.spotify.getPlaylistUris(self.playlistId)
        print('got playlist uris')

        # add missing uris to playlsit 
        missingUris = self.missingUris(artistSongUris, playlistUris)
        print(f"adding {len(missingUris)} new songs")
        self.spotify.addSongs(self.playlistId, missingUris)
        print("done")

    def getArtistSongs(self):
        '''
        extracts song uris from library based on artist uri
        '''
        # make dictionary of {'artist uri': [song uris]}
        # note can't use dict.fromkeys(list,value), each of these keys reference a single list
        self.artistSongDict = {k:[] for k in self.artistUris}
        # tracks from library are given in pages of info, max 50 items each iteration 
        # search page results for artist uri
        # add song uri to artist key if match found 
        self.spotify.getAllTracks(self.callback)

        # concatenate artist uris and remove duplicates 
        artistSongs = []
        for k in self.artistSongDict:
            artistSongs += self.artistSongDict[k]
        # pythonic and fast way to remove duplicates 
        # make into dictionary keys and then back into list
        artistSongs = list(dict.fromkeys(artistSongs))
        return artistSongs

    def callback(self, responseItems):
        # check each track in response
        for item in responseItems:
            track = item['track']
            # get artist uris for track 
            artistUris = self.spotify.getArtistFromTrack(track)
            # check each artist uri for match 
            for uri in artistUris:
                if uri in self.artistUris:
                    # if match add song uri
                    songUri = self.spotify.getSongUriFromTrack(track)
                    self.artistSongDict[uri].append(songUri)


if __name__ == "__main__":
    # update Recents Playlist 
    # recents = RecentPlaylist()
    # recents.update()

    # update artist playlist
    playlistId = 1
    manager = PlaylistManager(playlistId)
    manager.update()

