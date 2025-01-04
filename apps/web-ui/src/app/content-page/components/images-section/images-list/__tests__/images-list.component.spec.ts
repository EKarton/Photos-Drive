import { TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';

import { RESIZE_OBSERVER_FACTORY_TOKEN } from '../../../../../app.tokens';
import { MockResizeObserverFactory } from '../../../../../shared/resize-observer-factory/__mocks__/MockResizeObserverFactory';
import { ImageData, ImagesListComponent } from '../images-list.component';

const SAMPLE_IMAGES: ImageData[] = [
  {
    id: 'image1',
    baseUrl: 'https://www.google.com/photos/1',
    width: 4032,
    height: 3024,
    fileName: 'Image-1.pngs',
    onClick: jasmine.createSpy(),
    onKeyDown: jasmine.createSpy(),
  },
  {
    id: 'image2',
    baseUrl: 'https://www.google.com/photos/2',
    width: 3024,
    height: 4032,
    fileName: 'Image-1.pngs',
    onClick: jasmine.createSpy(),
    onKeyDown: jasmine.createSpy(),
  },
  {
    id: 'image3',
    baseUrl: 'https://www.google.com/photos/3',
    width: 5161,
    height: 3100,
    fileName: 'Image-1.pngs',
    onClick: jasmine.createSpy(),
    onKeyDown: jasmine.createSpy(),
  },
];

describe('ImagesListComponent', () => {
  let mockResizeObserverFactory: MockResizeObserverFactory;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ImagesListComponent],
      providers: [
        provideNoopAnimations(),
        {
          provide: RESIZE_OBSERVER_FACTORY_TOKEN,
          useValue: new MockResizeObserverFactory(),
        },
      ],
    }).compileComponents();

    mockResizeObserverFactory = TestBed.inject(
      RESIZE_OBSERVER_FACTORY_TOKEN,
    ) as MockResizeObserverFactory;
  });

  it('should render images', () => {
    const fixture = TestBed.createComponent(ImagesListComponent);
    fixture.componentRef.setInput('images', SAMPLE_IMAGES);
    fixture.detectChanges();

    const elements = fixture.nativeElement.querySelectorAll('img');
    expect(elements.length).toEqual(3);
    expect(elements[0].src).toEqual('https://www.google.com/photos/1');
    expect(elements[1].src).toEqual('https://www.google.com/photos/2');
    expect(elements[2].src).toEqual('https://www.google.com/photos/3');

    const component = fixture.componentInstance;
    expect(component).toBeTruthy();
  });

  it('should call onKeyDown() when user presses key on an image', () => {
    const fixture = TestBed.createComponent(ImagesListComponent);
    fixture.componentRef.setInput('images', SAMPLE_IMAGES);
    fixture.detectChanges();

    const image = fixture.nativeElement.querySelector('img');
    const event = new KeyboardEvent('keydown', { key: 'Enter' });
    image.dispatchEvent(event);

    expect(SAMPLE_IMAGES[0].onKeyDown).toHaveBeenCalledWith(event);
  });

  it('should call onClick() when user clicks on an image', () => {
    const fixture = TestBed.createComponent(ImagesListComponent);
    fixture.componentRef.setInput('images', SAMPLE_IMAGES);
    fixture.detectChanges();

    const image = fixture.nativeElement.querySelector('img');
    const event = new MouseEvent('click', {
      bubbles: true,
      cancelable: true,
      view: window,
    });
    image.dispatchEvent(event);

    expect(SAMPLE_IMAGES[0].onClick).toHaveBeenCalledWith(event);
  });

  [
    {
      hostElementWidth: 200,
      expectedImageWidths: [200, 200, 200],
      expectedImageHeights: [150, 267, 120],
    },
    {
      hostElementWidth: 500,
      expectedImageWidths: [245, 245, 245],
      expectedImageHeights: [184, 327, 147],
    },
    {
      hostElementWidth: 1200,
      expectedImageWidths: [393, 393, 393],
      expectedImageHeights: [295, 524, 236],
    },
    {
      hostElementWidth: 1600,
      expectedImageWidths: [392, 392, 392],
      expectedImageHeights: [294, 523, 235],
    },
  ].forEach(
    ({ hostElementWidth, expectedImageWidths, expectedImageHeights }) => {
      it(`should resize images correctly when the component width changes to ${hostElementWidth}`, async () => {
        // Render the component
        const fixture = TestBed.createComponent(ImagesListComponent);
        fixture.componentRef.setInput('images', SAMPLE_IMAGES);
        fixture.detectChanges();

        // Simulate a resize event
        const entry: ResizeObserverEntry = {
          borderBoxSize: [],
          contentBoxSize: [],
          contentRect: {
            bottom: 0,
            height: 0,
            left: 0,
            right: 0,
            top: 0,
            width: hostElementWidth,
            x: 0,
            y: 0,
            toJSON: () => Object,
          },
          devicePixelContentBoxSize: [],
          target: fixture.nativeElement,
        };

        // Trigger the observer's callback
        mockResizeObserverFactory.getInstances()[0].trigger([entry]);
        fixture.detectChanges();

        // Assert the images resized correctly
        const elements: HTMLImageElement[] = Array.from(
          fixture.nativeElement.querySelectorAll('img'),
        );
        const widths = Array.from(elements).map((e) => e.width);
        const heights = Array.from(elements).map((e) => e.height);
        expect(widths).toEqual(expectedImageWidths);
        expect(heights).toEqual(expectedImageHeights);
      });
    },
  );
});
