/**
 * A function that sets up the environment variables.
 *
 * @param newEnv the new environment variables
 * @returns a function which restores the environment variables.
 */
export function setupTestEnv(newEnv: object): cleanupTestEnvFn {
  const originalEnv = process.env;
  process.env = {
    ...originalEnv,
    ...newEnv
  };

  return () => {
    process.env = originalEnv;
  };
}

export type cleanupTestEnvFn = () => void;
