import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Store } from '@ngrx/store';
import { of } from 'rxjs';

import { WINDOW } from '../../../../../app.tokens';
import { gPhotosMediaItemsActions } from '../../../../store/gphoto-media-items';
import { mediaItemsActions } from '../../../../store/media-items';
import { mediaViewerActions } from '../../../../store/media-viewer';
import { ImageComponent } from './image.component';

describe('ImageComponent', () => {
  let component: ImageComponent;
  let fixture: ComponentFixture<ImageComponent>;
  let mockStore: jasmine.SpyObj<Store>;
  let mockWindow: jasmine.SpyObj<Window>;

  const mockMediaItem = {
    id: 'media-item-1',
    gPhotosMediaItemId: 'gphotos-item-1',
    fileName: 'test-image.jpg',
  };

  const mockGPhotosMediaItem = {
    baseUrl: 'http://test-url',
    mediaMetadata: { width: 1000, height: 800 },
  };

  beforeEach(async () => {
    mockStore = jasmine.createSpyObj('Store', ['select', 'dispatch']);
    mockWindow = jasmine.createSpyObj('Window', ['open']);

    await TestBed.configureTestingModule({
      declarations: [ImageComponent],
      providers: [
        { provide: Store, useValue: mockStore },
        { provide: WINDOW, useValue: mockWindow },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ImageComponent);
    component = fixture.componentInstance;
  });

  describe('Initialization', () => {
    it('should create', () => {
      expect(component).toBeTruthy();
    });

    it('should dispatch media item details when in viewport', () => {
      mockStore.select.and.returnValue(
        of({ status: 'success', data: mockMediaItem }),
      );

      component.mediaItemId.set('media-item-1');
      component.width.set(500);
      component.setIsInViewport(true);

      expect(mockStore.dispatch).toHaveBeenCalledWith(
        mediaItemsActions.loadMediaItemDetails({ mediaItemId: 'media-item-1' }),
      );
    });
  });

  describe('Image Opening', () => {
    beforeEach(() => {
      mockStore.select.and.returnValues(
        of({ status: 'success', data: mockMediaItem }),
        of({ status: 'success', data: mockGPhotosMediaItem }),
      );
      component.mediaItemId.set('media-item-1');
      component.width.set(500);
    });

    it('should open image in new tab with ctrl+click', () => {
      const mockEvent = new MouseEvent('click', { ctrlKey: true });
      const imageData = component.imageDataResult();

      if (imageData.status === 'success') {
        imageData.data.onClick(mockEvent);
        expect(mockWindow.open).toHaveBeenCalledWith(
          `${mockGPhotosMediaItem.baseUrl}=w${mockGPhotosMediaItem.mediaMetadata.width}-h${mockGPhotosMediaItem.mediaMetadata.height}`,
          '_blank',
        );
      }
    });

    it('should open image in dialog on regular click', () => {
      const mockEvent = new MouseEvent('click');
      const imageData = component.imageDataResult();

      if (imageData.status === 'success') {
        imageData.data.onClick(mockEvent);
        expect(mockStore.dispatch).toHaveBeenCalledWith(
          mediaViewerActions.openMediaViewer({
            request: { mediaItemId: 'media-item-1' },
          }),
        );
      }
    });
  });

  describe('Viewport Behavior', () => {
    it('should not dispatch when not in viewport', () => {
      mockStore.select.and.returnValue(
        of({ status: 'success', data: mockMediaItem }),
      );

      component.mediaItemId.set('media-item-1');
      component.width.set(500);
      component.setIsInViewport(false);

      expect(mockStore.dispatch).not.toHaveBeenCalled();
    });
  });

  describe('Image Size Calculation', () => {
    it('should calculate correct image height', () => {
      mockStore.select.and.returnValues(
        of({ status: 'success', data: mockMediaItem }),
        of({ status: 'success', data: mockGPhotosMediaItem }),
      );
      component.mediaItemId.set('media-item-1');
      component.width.set(500);

      const imageData = component.imageDataResult();

      if (imageData.status === 'success') {
        expect(imageData.data.width).toBe(500);
        expect(imageData.data.height).toBe(400); // (800/1000) * 500
      }
    });
  });
});
