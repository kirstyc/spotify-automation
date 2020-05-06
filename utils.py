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
    # general send utils
    ###################

    def sendRequestLimited(self, data, limit, playlistId, sendCallback):
        # TODO Compare this with get request limited
        dataMatrix = [data[i:i+limit] for i in range(0, len(data), limit)]

        for data in dataMatrix:
           sendCallback(playlistId, data)

        return

    ###################
    # Get Playlist Info 
    ###################

    def getSavedTrackRequest(self, query):

        response = requests.get(
            query,
            headers = self.headers
        )
        responseJson = self.unpack(response)

        return responseJson

    def getAllTracks(self, pageCallback):
        songLimit = 50 
        query = f"https://api.spotify.com/v1/me/tracks?limit={songLimit}"
        while query is not None:
            print(f"GET {query}")
            response = self.getSavedTrackRequest(query)
            pageCallback(response['items'])
            query = response['next']
         
    def getLatestTracks(self, numSongs):
        # TODO retest 
        query = f"https://api.spotify.com/v1/me/tracks?limit={numSongs}"
        response = self.getSavedTrackRequest(query)
        items = response['items']

        return items

    def getLatestTrackUris(self, numSongs):
        '''
        returns spotify uris of the latest saved tracks 
        '''
        tracks = self.getLatestTracks(numSongs)
        uris = []
        for item in tracks:
            uris.append(self.getSongUriFromTrack(item))
        
        return uris

    ###################
    # Get OveraLL Playlist Info 
    ###################

    def getPlaylists(self):
        '''
        returns all data related to playlists
        '''
        # TODO check if this has fields
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

    def getPlaylistIdFromName(self, name):
        names = self.getPlaylistNames()
        return names[name]

    ###################
    # Get Specific Playlist Info 
    ###################

    def getPlaylistItemsRequest(self, playlistId, trackLimit = 100, fields = None, query = None):

        if query is None:
            query = f'https://api.spotify.com/v1/playlists/{playlistId}/tracks'
        queryParams = {
            'limit' : trackLimit
        }

        # can specify fields to get specific info
        if fields is not None:
            queryParams['fields'] = fields

        response = requests.get(
            query,
            params = queryParams,
            headers = self.headers
        )
        responseJson = self.unpack(response)
        return responseJson

    def getPlaylistItemsAll(self, playlistId, itemFields):

        items = []
        f = itemFields + ',next'
        q = None
        nextUrl  = True
        while nextUrl is not None:
            response = self.getPlaylistItemsRequest(playlistId, fields = f, query = q)
            items += response['items']
            nextUrl = response['next']
            q = nextUrl

        return items 

    def getPlaylistUris(self, playlistId, trackLimit = 100):
        itemFields = 'items.track.uri'
        playlistItems = self.getPlaylistItemsAll(playlistId, itemFields)
        uris = []
        for item in playlistItems:
            uris.append(self.getSongUriFromTrack(item))
        return uris

    def getPlaylistAddDates(self, playlistId, trackLimit = 100):
        '''
        returns {'add date':uri} for tracks in playlist
        '''
        itemFields = 'items(added_at,track(uri))'
        playlistItems = self.getPlaylistItemsAll(playlistId, itemFields)
        dates = {}
        for item in playlistItems:
            dates[item['added_at']] = self.getSongUriFromTrack(item)
        return dates

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

        # can only add 100 songs at a time 
        songLimit = 100
        self.sendRequestLimited(uris, songLimit, playlistId, self.addSongsRequest)

        return 

    def addSongsRequest(self, playlistId, uris):
        query = f"https://api.spotify.com/v1/playlists/{playlistId}/tracks"

        uris = json.dumps(uris)

        response = requests.post(
            query,
            data = uris,
            headers = self.headers
        )

        return self.unpack(response)

    def removeSongs(self, playlistId, uris):
        songLimit = 100 
        self.sendRequestLimited(uris, songLimit, playlistId, self.removeSongsRequest)
        return 

    def removeSongsRequest(self, playlistId, uris):

        query = f"https://api.spotify.com/v1/playlists/{playlistId}/tracks"

        queryParams = json.dumps({"tracks":[{"uri":item} for item in uris ]})

        response = requests.delete(
            query,
            data = queryParams,
            headers = self.headers
        )

        return self.unpack(response)


    ###################
    # Get Song Info 
    ###################

    def searchSpotify(self, songTitle, artist):

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

    def getSongUriFromTrack(self, track):
        try:
            track = track['track']
        except:
            pass
        
        return track['uri']

    ###################
    # Get Artist Info 
    ###################

    def getArtistUri(self, artist):

        query = f"https://api.spotify.com/v1/search?q={artist}&type=artist"

        response = requests.get(
            query,
            headers= self.headers
        )
        responseJson = self.unpack(response)

        artists = responseJson["artists"]["items"]
        uri = artists[0]["uri"]

        return uri 

    def getArtistUris(self, artists):
        
        uris = [self.getArtistUri(artist) for artist in artists]
        return uris 

    def getArtistFromTrack(self, track):
        '''
        extracts artist uri from track object 
        '''
        try:
            track = track['track']
        except:
            pass
        
        uris = []
        for artist in track['artists']:
            uris.append(artist['uri'])

        return uris

