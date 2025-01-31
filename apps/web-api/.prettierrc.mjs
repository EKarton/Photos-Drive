export default {
  semi: true,
  singleQuote: true,
  trailingComma: 'none',
  plugins: ['@ianvs/prettier-plugin-sort-imports'],
  importOrder: ['^react', '^@?\\w', '^components/(.*)$', '^[./]']
};
