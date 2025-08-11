export default {
  testEnvironment: 'jest-environment-node-single-context',
  verbose: true,
  transform: {
    '^.+\\.tsx?$': 'ts-jest'
  },
  coverageThreshold: {
    global: {
      branches: 100,
      functions: 99,
      lines: 100,
      statements: 99
    }
  }
};
