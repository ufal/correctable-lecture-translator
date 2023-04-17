module.rules = [
  {
    test: /\.pug$/,
    loader: 'pug-plain-loader'
  },
  {
    test: /\.scss$/,
    use: [
      'vue-style-loader',
      'css-loader',
      'sass-loader'
    ]
  }
]