# Propagation and Extrapolation

The track propagation is one essitial part of each track reconstruction software. The ACTS propgation code is based on the ATLAS `RungeKuttaPropagator` which is still availalbe in the `Legacy` 

## Steppers and Propgator

The ACTS propagator allows for different `Stepper` implementations provided as a class template.
Following the general ACTS design, each stepper has a nested cache struct, which is used for caching the field cell and
the update the jacobian for covariance propagation.

### AtlasStepper

The `AtlasStepper` is a pure transcript from the ATLAS `RungeKuttaPropagator` and `RungeKuttaUtils`, and operators with an internal structure of `double[]`. This example shows a code snippet from the numerical integration.

    while (h != 0.) {
      double S3 = (1. / 3.) * h, S4 = .25 * h, PS2 = Pi * h;

      // First point
      //
      double H0[3] = {f0[0] * PS2, f0[1] * PS2, f0[2] * PS2};
      double A0    = A[1] * H0[2] - A[2] * H0[1];
      double B0    = A[2] * H0[0] - A[0] * H0[2];
      double C0    = A[0] * H0[1] - A[1] * H0[0];
      double A2    = A0 + A[0];
      double B2    = B0 + A[1];
      double C2    = C0 + A[2];
      double A1    = A2 + A[0];
      double B1    = B2 + A[1];
      double C1    = C2 + A[2];

      // Second point
      //
      if (!Helix) {
        const Vector3D pos(R[0] + A1 * S4, R[1] + B1 * S4, R[2] + C1 * S4);
        f = getField(cache, pos);
      } else {
        f = f0;
      }

      double H1[3] = {f[0] * PS2, f[1] * PS2, f[2] * PS2};
      double A3    = (A[0] + B2 * H1[2]) - C2 * H1[1];
      double B3    = (A[1] + C2 * H1[0]) - A2 * H1[2];
      double C3    = (A[2] + A2 * H1[1]) - B2 * H1[0];
      double A4    = (A[0] + B3 * H1[2]) - C3 * H1[1];
      double B4    = (A[1] + C3 * H1[0]) - A3 * H1[2];
      double C4    = (A[2] + A3 * H1[1]) - B3 * H1[0];
      double A5    = 2. * A4 - A[0];
      double B5    = 2. * B4 - A[1];
      double C5    = 2. * C4 - A[2];

      // Last point
      //
      if (!Helix) {
        const Vector3D pos(R[0] + h * A4, R[1] + h * B4, R[2] + h * C4);
        f = getField(cache, pos);
      } else {
        f = f0;
      }

      double H2[3] = {f[0] * PS2, f[1] * PS2, f[2] * PS2};
      double A6    = B5 * H2[2] - C5 * H2[1];
      double B6    = C5 * H2[0] - A5 * H2[2];
      double C6    = A5 * H2[1] - B5 * H2[0];
      
      

### EigenStepper

The `EigenStepper` implements the same functionality as the ATLAS stepper, however, the stepping code 
is rewritten with using `Eigen` primitives. The following code snippet shows the full Runge-Kutta stepping code. 

    // The following functor starts to perform a Runge-Kutta step of a certain
    // size, going up to the point where it can return an estimate of the local
    // integration error. The results are cached in the local variables above,
    // allowing integration to continue once the error is deemed satisfactory
    const auto tryRungeKuttaStep = [&](const double h) -> double {
      // Cache the square and half of the step size
      h2     = h * h;
      half_h = h / 2;

      // Second Runge-Kutta point
      const Vector3D pos1 = cache.pos + half_h * cache.dir + h2 / 8 * k1;
      B_middle            = getField(cache, pos1);
      k2                  = qop * (cache.dir + half_h * k1).cross(B_middle);

      // Third Runge-Kutta point
      k3 = qop * (cache.dir + half_h * k2).cross(B_middle);

      // Last Runge-Kutta point
      const Vector3D pos2 = cache.pos + h * cache.dir + h2 / 2 * k3;
      B_last              = getField(cache, pos2);
      k4                  = qop * (cache.dir + h * k3).cross(B_last);

      // Return an estimate of the local integration error
      return h * (k1 - k2 - k3 + k4).template lpNorm<1>();
    };