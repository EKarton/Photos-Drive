import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';

import { FeatureFlags, FeatureFlagsService } from '../feature-flags.service';

describe('FeatureFlagsService', () => {
  let service: FeatureFlagsService;
  let router: Router;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [FeatureFlagsService, provideRouter([])],
    });

    service = TestBed.inject(FeatureFlagsService);
    router = TestBed.inject(Router);
  });

  it('should create the service and have flags initialized', async () => {
    const events: boolean[] = [];
    service
      .isEnabled$(FeatureFlags.NewImagesListView)
      .subscribe((isEnabled) => {
        events.push(isEnabled);
      });
    expect(service.isEnabled(FeatureFlags.NewImagesListView)).toBeFalse();
    expect(events).toEqual([false]);
  });

  it('should set flags to true when query param has flags', async () => {
    await router.navigate([], {
      queryParams: { [FeatureFlags.NewImagesListView]: 'true' },
    });

    const events: boolean[] = [];
    service
      .isEnabled$(FeatureFlags.NewImagesListView)
      .subscribe((isEnabled) => {
        events.push(isEnabled);
      });

    expect(service.isEnabled(FeatureFlags.NewImagesListView)).toBeTrue();
    expect(events).toEqual([true]);
  });

  it('should update flags on navigation change event', async () => {
    await router.navigate([], {
      queryParams: { [FeatureFlags.NewImagesListView]: 'true' },
    });
    const events: boolean[] = [];
    service
      .isEnabled$(FeatureFlags.NewImagesListView)
      .subscribe((isEnabled) => {
        events.push(isEnabled);
      });

    await router.navigate([], {
      queryParams: { [FeatureFlags.NewImagesListView]: 'false' },
    });

    expect(service.isEnabled(FeatureFlags.NewImagesListView)).toBeFalse();
    expect(events).toEqual([true, false]);
  });
});
