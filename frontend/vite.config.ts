// Plugins
import vue from "@vitejs/plugin-vue";
import vuetify, { transformAssetUrls } from "vite-plugin-vuetify";

// Utilities
import { defineConfig } from "vite";
import { fileURLToPath, URL } from "node:url";

import fs from "fs";

let serverKey: Buffer;
let serverCert: Buffer;
let serverConfig;
let port = 5001;

try {
	serverKey = fs.readFileSync(process.env.SERVERKEY!);
	serverCert = fs.readFileSync(process.env.SERVERCERT!);

	serverConfig = {
		port: port,
		https: {
			key: serverKey,
			cert: serverCert,
		},
	};
	console.info("Running https server.");
} catch (e) {
	console.error(e);
	console.info("Running http server without SSL.");

	serverConfig = {
		port: port,
	};
}

// https://vitejs.dev/config/
export default defineConfig({
	plugins: [
		vue({
			template: { transformAssetUrls },
		}),
		// https://github.com/vuetifyjs/vuetify-loader/tree/next/packages/vite-plugin
		vuetify({
			autoImport: true,
			styles: {
				configFile: "src/styles/settings.scss",
			},
		}),
	],
	define: { "process.env": {} },
	resolve: {
		alias: {
			"@": fileURLToPath(new URL("./src", import.meta.url)),
		},
		extensions: [".js", ".json", ".jsx", ".mjs", ".ts", ".tsx", ".vue"],
	},
	server: serverConfig,
});
