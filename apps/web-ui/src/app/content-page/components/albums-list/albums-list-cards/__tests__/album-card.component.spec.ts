import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import {
  toFailure,
  toPending,
  toSuccess,
} from '../../../../../shared/results/results';
import { Album } from '../../../../services/albums';
import { AlbumsListCardsComponent } from '../albums-list-cards.component';

const ALBUM_DETAILS_1: Album = {
  id: 'album1',
  albumName: '2010',
  parentAlbumId: 'album1',
  childAlbumIds: [],
  numChildAlbums: 0,
  numMediaItems: 1,
};

const ALBUM_DETAILS_2: Album = {
  id: 'album2',
  albumName: '2011',
  parentAlbumId: 'album1',
  childAlbumIds: [],
  numChildAlbums: 0,
  numMediaItems: 1,
};

const ALBUM_DETAILS_3: Album = {
  id: 'album3',
  albumName: '2012',
  parentAlbumId: 'album1',
  childAlbumIds: [],
  numChildAlbums: 0,
  numMediaItems: 1,
};

describe('AlbumsListCardsComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AlbumsListCardsComponent],
      providers: [provideRouter([])],
    }).compileComponents();
  });

  it('should render skeleton when albums are not loaded yet', () => {
    const fixture = TestBed.createComponent(AlbumsListCardsComponent);
    fixture.componentRef.setInput('albums', [
      toPending(),
      toPending(),
      toPending(),
    ]);
    fixture.detectChanges();

    const skeletons = fixture.nativeElement.querySelectorAll(
      '[data-testid="album-skeleton"]',
    );
    expect(skeletons.length).toEqual(3);
  });

  it('should show error when albums has failed to load', () => {
    const fixture = TestBed.createComponent(AlbumsListCardsComponent);
    fixture.componentRef.setInput('albums', [
      toFailure(new Error('Random error')),
      toFailure(new Error('Random error')),
      toFailure(new Error('Random error')),
    ]);
    fixture.detectChanges();

    const error = fixture.nativeElement.querySelector(
      '[data-testid="albums-error"]',
    );
    expect(error).toBeTruthy();
  });

  it('should render correctly when child albums has loaded already', () => {
    const fixture = TestBed.createComponent(AlbumsListCardsComponent);
    fixture.componentRef.setInput('albums', [
      toSuccess(ALBUM_DETAILS_1),
      toSuccess(ALBUM_DETAILS_2),
      toSuccess(ALBUM_DETAILS_3),
    ]);
    fixture.detectChanges();

    const subAlbums = fixture.nativeElement.querySelectorAll(
      '[data-testid="album"]',
    );
    expect(subAlbums.length).toEqual(3);
  });
});
