export default {
  semi: false,
  singleQuote: true,
  trailingComma: 'none',
  plugins: ['@ianvs/prettier-plugin-sort-imports'],
  importOrder: ['^react', '^@?\\w', '^components/(.*)$', '^[./]']
}
