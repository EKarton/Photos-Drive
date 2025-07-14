export interface GetMapTileRequest {
  x: number;
  y: number;
  z: number;
  albumId: string | undefined;
}

export interface GetMapTileResponse {
  mediaItemId: string | undefined;
  numMediaItems: number;
}
