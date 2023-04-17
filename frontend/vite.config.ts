// Plugins
import vue from '@vitejs/plugin-vue';
import vuetify, { transformAssetUrls } from 'vite-plugin-vuetify';

// Utilities
import { defineConfig } from 'vite';
import { fileURLToPath, URL } from 'node:url';

import fs from 'fs';

let serverKey: Buffer;
let serverCert: Buffer;
let serverConfig;

try {
  serverKey = fs.readFileSync(process.env.SERVERKEY!);
  serverCert = fs.readFileSync(process.env.SERVERCERT!);

  serverConfig = {
    port: 5001,
    https: {
      key: serverKey,
      cert: serverCert
    },
  }
}
catch (e) {
  console.error(e);
  console.info("Running http server without SSL.")

  serverConfig = {
    port: 5001,
  }
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue({
      template: { transformAssetUrls }
    }),
    // https://github.com/vuetifyjs/vuetify-loader/tree/next/packages/vite-plugin
    vuetify({
      autoImport: true,
      styles: {
        configFile: 'src/styles/settings.scss',
      },
    }),
  ],
  define: { 'process.env': {} },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
    extensions: [
      '.js',
      '.json',
      '.jsx',
      '.mjs',
      '.ts',
      '.tsx',
      '.vue',
    ],
  },
  server: serverConfig,
})
