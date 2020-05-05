import json
import requests

class ResponseException(Exception):
    def __init__(self, status_code, message=""):
        self.message = message
        self.status_code = status_code

    def __str__(self):
        return self.message + f"Response gave status code {self.status_code}"

class SpotifyUtils():
    
    def __init__(self):
        self.credentialsFile = "credentials.json"
        self.username = self.getUsername()
        self.spotifyToken = self.getSpotifyToken()
        self.headers = self.getHeaders()

    ###################
    # Credentials
    ###################

    def getUsername(self):
        jsonDict = self.getJson()
        return jsonDict['username'] 

    def getSpotifyToken(self):
        jsonDict = self.getJson()
        return jsonDict['oauth-token'] 

    def getJson(self):
        with open(self.credentialsFile) as f:
            data = json.load(f)
        return data

    def getHeaders(self):
        headers = {
                "Content-Type" : "application/json",
                "Authorization" : f"Bearer {self.spotifyToken}"
            }
        return headers

    ###################
    # unpack response
    ###################

    def unpack(self, response):
        self.checkResponse(response)
        return response.json()

    def checkResponse(self, response):
        # check for valid response status 
        if response.status_code not in range(200,205):
            raise ResponseException(response.status_code)

    ###################
    # Get Playlist Info 
    ###################

    def getSavedTracks(self, numSongs):
        '''
        returns latest saved tracks from user 
        '''

        query = "https://api.spotify.com/v1/me/tracks"
        queryParams = {
            "limit" : numSongs
        }

        response = requests.get(
            query,
            params = queryParams,
            headers = self.headers
        )
        responseJson = self.unpack(response)

        return responseJson['items']

    def getSavedTrackUris(self, numSongs):
        '''
        returns spotify uris of the latest saved tracks 
        '''
        tracks = self.getSavedTracks(numSongs)
        uris = []
        for item in tracks:
            uris.append(item['track']['uri'])
        
        return uris

    ###################
    # Get OveraLL Playlist Info 
    ###################

    def getPlaylists(self):
        '''
        returns all data related to playlists
        '''
        query = "https://api.spotify.com/v1/me/playlists"

        response = requests.get(
            query,
            headers = self.headers
        )

        return self.unpack(response)

    def getPlaylistTotal(self):
        '''
        gets the total number of user playlists
        '''
        playlists = self.getPlaylists()
        return playlists['total']

    def getPlaylistNames(self):
        '''
        gets all playlist names as a dictionary
        {
            'playlist name': playlist_id
        }
        '''
        playlists = self.getPlaylists()
        names = {}
        for item in playlists['items']:
            key = item['name']
            val = item['id']
            names[key] = val
        
        return names 

    ###################
    # Get Specific Playlist Info 
    ###################

    def getPlaylistItems(self, playlistId, trackLimit = 100):

        query = f'https://api.spotify.com/v1/playlists/{playlistId}/tracks'
        queryParams = {
            'limit' : trackLimit
        }

        response = requests.get(
            query,
            params = queryParams,
            headers = self.headers
        )
        responseJson = self.unpack(response)
        return responseJson['items']

    def getPlaylistUris(self, playlistId, trackLimit = 100):
        playlistItems = self.getPlaylistItems(playlistId, trackLimit)
        uris = []
        for item in playlistItems:
            uris.append(item['track']['uri'])
        return uris

    def getPlaylistAddDates(self, playlistId, trackLimit = 100):
        '''
        returns {'add date':uri} for tracks in playlist
        '''
        playlistItems = self.getPlaylistItems(playlistId, trackLimit)
        dates = {}
        for item in playlistItems:
            dates[item['added_at']] = item['track']['uri']
        return dates

    ###################
    # Get Song Info 
    ###################

    def getSpotifyUri(self, songTitle, artist):

        query = f"https://api.spotify.com/v1/search?query=track%3A{songTitle}+artist%3A{artist}&type=track&offset=0&limit=20"
        
        response = requests.get(
            query,
            headers= self.headers
        )
        responseJson = self.unpack(response)

        songs = responseJson["tracks"]["items"]
        # only use the first song
        uri = songs[0]["uri"]

        return uri

    ###################
    # Sets Playlist Data
    ###################

    def createPlaylist(self, name, desc, public = False):
        
        requestBody = json.dumps(
            {
                "name" : name,
                "description": desc,
                "public" : public
            }
        )

        query = f"https://api.spotify.com/v1/users/{self.username}/playlists"

        response = requests.post(
            query,
            data = requestBody,
            headers = self.headers
        )
        responseJson = self.unpack(response)

        # playlist id 
        return responseJson["id"]

    def addSongs(self, playlistId, uris):

        query = f"https://api.spotify.com/v1/playlists/{playlistId}/tracks"

        uris = json.dumps(uris)

        response = requests.post(
            query,
            data = uris,
            headers = self.headers
        )

        return self.unpack(response)

    def removeSongs(self, playlistId, uris):

        query = f"https://api.spotify.com/v1/playlists/{playlistId}/tracks"

        queryParams = json.dumps({"tracks":[{"uri":item} for item in uris ]})

        response = requests.delete(
            query,
            data = queryParams,
            headers = self.headers
        )

        return self.unpack(response)