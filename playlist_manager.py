from utils import SpotifyUtils

class RecentPlaylist():
    
    def __init__(self):
        self.name = 'Recents'
        self.desc = 'Recently added music'
        self.numSongs = 20
        self.spotify = SpotifyUtils()
        self.id = self.getId()

    def getId(self):
        names = self.spotify.getPlaylistNames()
        if self.name in names:
            playlistId = names[self.name]
        else:
            playlistId = self.create()

        return playlistId 

    def create(self):
        playlistId = self.spotify.createPlaylist(self.name, self.desc)
        return playlistId

    def update(self):
        
        # get latest tracks
        print(f"for {self.name} Playlist: id={self.id}")
        latestUris = self.spotify.getSavedTrackUris(self.numSongs)
        print(f"got {self.numSongs} latest saved tracks")

        # check which tracks are new to playlist 
        playlistUris = self.spotify.getPlaylistUris(self.id)
        print(f"got current tracks from {self.name}")
        missingUris = []
        for newUri in latestUris:
            if newUri not in playlistUris:
                missingUris.append(newUri)
        print(f"{len(missingUris)} new tracks to add")

        # remove old songs
        numRemove = abs(self.numSongs - len(playlistUris) - len(missingUris))
        if numRemove > 0:
            datesAddedDict = self.spotify.getPlaylistAddDates(self.id)
            datesAdded = list(datesAddedDict.keys()).sort()
            oldDates = datesAdded[:numRemove]
            removeUris = [datesAddedDict[date] for date in oldDates]
            self.spotify.removeSongs(self.id, removeUris)
            print(f"{numRemove} old songs removed")

        # add new songs 
        self.spotify.addSongs(self.id, missingUris)
        print("added new tracks")
    

if __name__ == "__main__":
    recents = RecentPlaylist()
    recents.update()
