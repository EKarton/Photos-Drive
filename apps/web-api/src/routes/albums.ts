import { wrap } from 'async-middleware';
import { Request, Response, Router } from 'express';
import { verifyAuthentication } from '../middlewares/authentication';
import { verifyAuthorization } from '../middlewares/authorization';
import {
  Album,
  AlbumId,
  albumIdToString,
  convertStringToAlbumId
} from '../services/metadata_store/Albums';
import {
  AlbumNotFoundError,
  AlbumsRepository,
  SortByDirection,
  SortByField
} from '../services/metadata_store/AlbumsRepository';
import { MediaItemsRepository } from '../services/metadata_store/MediaItemsRepository';
import { MongoDbClientNotFoundError } from '../services/metadata_store/mongodb/MongoDbClientsRepository';
import parseEnumOrElse from '../utils/parseEnumOrElse';

export default async function (
  rootAlbumId: AlbumId,
  albumsRepo: AlbumsRepository,
  mediaItemsRepo: MediaItemsRepository
) {
  const router: Router = Router();

  router.get(
    '/api/v1/albums',
    await verifyAuthentication(),
    await verifyAuthorization(),
    wrap(async (req: Request, res: Response) => {
      const pageSize = Number(req.query['pageSize']);
      const pageToken = req.query['pageToken'] as string;
      const sortBy = req.query['sortBy'];
      const sortDir = req.query['sortDir'];
      const parentAlbumId = req.query['parentAlbumId'] as string;

      const response = await albumsRepo.listAlbums({
        parentAlbumId: parentAlbumId
          ? convertStringToAlbumId(parentAlbumId)
          : undefined,
        pageSize: !isNaN(pageSize) ? Math.min(50, Math.max(0, pageSize)) : 25,
        pageToken: pageToken ? decodeURIComponent(pageToken) : undefined,
        sortBy: {
          field: parseEnumOrElse(SortByField, sortBy, SortByField.ID),
          direction: parseEnumOrElse(
            SortByDirection,
            sortDir,
            SortByDirection.ASCENDING
          )
        }
      });

      const [mediaItemCounts, childAlbumCounts] = await Promise.all([
        Promise.all(
          response.albums.map((album) =>
            mediaItemsRepo.getNumMediaItemsInAlbum(album.id)
          )
        ),
        Promise.all(
          response.albums.map((album) =>
            albumsRepo.getNumAlbumsInAlbum(album.id)
          )
        )
      ]);

      return res.status(200).json({
        albums: response.albums.map((album, i) =>
          serializeAlbum(album, childAlbumCounts.at(i)!, mediaItemCounts.at(i)!)
        ),
        nextPageToken: response.nextPageToken
          ? encodeURIComponent(response.nextPageToken)
          : undefined
      });
    })
  );

  router.get(
    '/api/v1/albums/root',
    await verifyAuthentication(),
    await verifyAuthorization(),
    wrap(async (_, res: Response) => {
      const rawAlbumId = `${rootAlbumId.clientId}:${rootAlbumId.objectId}`;
      return res.redirect(`/api/v1/albums/${rawAlbumId}`);
    })
  );

  router.get(
    '/api/v1/albums/:albumId',
    await verifyAuthentication(),
    await verifyAuthorization(),
    wrap(async (req: Request, res: Response) => {
      try {
        const albumId = convertStringToAlbumId(req.params.albumId);
        const [album, numChildAlbums, numMediaItems] = await Promise.all([
          albumsRepo.getAlbumById(albumId),
          albumsRepo.getNumAlbumsInAlbum(albumId),
          mediaItemsRepo.getNumMediaItemsInAlbum(albumId)
        ]);

        return res
          .status(200)
          .json(serializeAlbum(album, numChildAlbums, numMediaItems));
      } catch (error) {
        if (error instanceof MongoDbClientNotFoundError) {
          return res.status(404).json({ error: 'Album not found' });
        }
        if (error instanceof AlbumNotFoundError) {
          return res.status(404).json({ error: 'Album not found' });
        }

        throw error;
      }
    })
  );

  return router;
}

function serializeAlbum(
  album: Album,
  numChildAlbums: number,
  numMediaItems: number
): object {
  return {
    id: `${album.id.clientId}:${album.id.objectId}`,
    albumName: album.name,
    parentAlbumId: album.parent_album_id
      ? albumIdToString(album.parent_album_id)
      : null,
    childAlbumIds: album.child_album_ids.map((id: AlbumId) =>
      albumIdToString(id)
    ),
    numChildAlbums,
    numMediaItems
  };
}
