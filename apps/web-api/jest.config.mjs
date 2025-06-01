export default {
  verbose: true,
  transform: {
    '^.+\\.tsx?$': 'ts-jest'
  },
  coverageThreshold: {
    global: {
      branches: 98,
      functions: 100,
      lines: 100,
      statements: 100
    }
  }
};
