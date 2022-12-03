from typing import List
from multipledispatch import dispatch
import discogs_client
from datalayer.artistnotfound import ArtistNotFound
from discogs_client.exceptions import HTTPError


class DiscogsBridge(object):
    @dispatch(str, str)
    def __init__(self, key: str, secret: str):
        self.__temp_collaborators: list[dict] = []
        self.__dc: discogs_client.Client = discogs_client.Client(
            'Name',
            consumer_key=key,
            consumer_secret=secret
        )

    @dispatch()
    def __init__(self):
        key = "[YOUR KEY]"
        secret = "YOUR SECRET"
        self.__temp_collaborators: list[dict] = []

        self.__dc: discogs_client.Client = discogs_client.Client(
            'Name',
            consumer_key=key,
            consumer_secret=secret
        )

    def get_artist_by_id(self, aid: int, year: int = 1935) -> dict:
        """
        Get a dictionary of information about an artist from Discogs
        :param aid: artist id
        :param year: optional year
        :return: dictionary with artist info
        :raises: ArtistNotFound if the artist is not found in Discogs
        """

        try:
            artist_object = self.__dc.artist(aid)

            artist_id: int = artist_object.id
            artist_name: str = artist_object.name
            artist_realname: str = artist_object.real_name if artist_object.real_name is not None else artist_object.name
            artist_profile: str = artist_object.profile
            artist_level = 0

            # Extra credit implementation: collaborations component returned too
            # collaboratorID, collaboratorName, releaseID, roles
            artist_collaborations: list[dict] = []

            # url
            artist_releases = artist_object.releases

            # check if artist_releases in the Artist class exists
            if artist_releases is not None:
                # store the collab ids from loops here, remove duplicates
                collab_ids = []

                # for each release objects in the release
                for release in artist_releases:
                    if hasattr(release, "year") and 0 < release.year <= year:
                        # loop through artist, extra_artists, and tracklist to find new collaborators
                        release_id = release.id
                        release_object = self.__dc.release(release_id)

                        # the artists loop
                        if hasattr(release_object, "artists") and release_object.artists is not None:
                            for artist in release_object.artists:
                                if artist.id != artist_id and artist.id not in collab_ids:
                                    collab_ids.append(artist.id)
                                    collab_entry = {
                                        "collaboratorID": artist.id,
                                        "collaboratorName": artist.name,
                                        "releaseID": release_id,
                                        "roles": [""]
                                    }
                                    artist_collaborations.append(collab_entry)

                        # the extra_artist loop
                        if hasattr(release_object, 'extraartists') and release_object.extraartists is not None:
                            for extra_artist in release_object.extraartists:
                                if extra_artist.id != artist_id and extra_artist.id not in collab_ids:
                                    collab_ids.append(extra_artist.id)
                                    collab_entry = {
                                        "collaboratorID": extra_artist.id,
                                        "collaboratorName": extra_artist.name,
                                        "releaseID": release_id,
                                        "roles": [extra_artist.role]
                                    }
                                    artist_collaborations.append(collab_entry)

                        # the tracklist loop
                        if hasattr(release_object, "tracklist") and release_object.tracklist is not None:
                            for track in release_object.tracklist:
                                extra_artist_list = track.fetch("extraartists")
                                if extra_artist_list is not None:
                                    for item in extra_artist_list:
                                        if item['id'] != artist_id and item['id'] not in collab_ids:
                                            collab_ids.append(item['id'])
                                            collab_entry = {
                                                "collaboratorID": item['id'],
                                                "collaboratorName": item['name'],
                                                "releaseID": release_id,
                                                "roles": [item['role']]
                                            }
                                            artist_collaborations.append(collab_entry)

            artist = {"artistID": artist_id, "artistName": artist_name, "realname": artist_realname,
                      "profile": artist_profile, "level": artist_level, "collaborators": artist_collaborations}

        except HTTPError:
            artist = {"artistID": aid, "artistName": "", "realname": "",
                      "profile": "", "level": "", "collaborators": []}
            raise ArtistNotFound("Can't find artist.", -1)
        return artist

    def get_artists_from_list(self, a_list: list[int], year: int = 1935) -> list[dict]:
        """
        Get all the artists from Discogs based on the input list of int ids
        :param a_list: list of integer ids
        :param year: year filter
        """
        result: List[dict] = []
        for i in a_list:
            a = self.get_artist_by_id(i, year)
            if a is not None:
                result.append(a)
        if not result:
            raise ArtistNotFound("No artists found", 404)
        else:
            return result
