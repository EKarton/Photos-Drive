import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';

import { FeatureFlags, FeatureFlagsService } from '../feature-flags.service';

describe('FeatureFlagsService (Angular 18+ router testing)', () => {
  let service: FeatureFlagsService;
  let router: Router;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [FeatureFlagsService, provideRouter([])],
    });

    service = TestBed.inject(FeatureFlagsService);
    router = TestBed.inject(Router);
  });

  it('should create the service and have flags initialized', () => {
    expect(service).toBeTruthy();
    expect(service.isEnabled(FeatureFlags.NewImagesListView)).toBeFalse();
  });

  it('should update flags on navigation change event', async () => {
    await router.navigate([], {
      queryParams: { [FeatureFlags.NewImagesListView]: 'true' },
    });

    expect(service.isEnabled(FeatureFlags.NewImagesListView)).toBeTrue();

    await router.navigate([], {
      queryParams: { [FeatureFlags.NewImagesListView]: 'false' },
    });

    expect(service.isEnabled(FeatureFlags.NewImagesListView)).toBeFalse();
  });
});
