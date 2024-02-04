<template lang="pug">
.textViewer
	.subTitle Text viewer
	.translation(v-html="getFinalText")
</template>

<script lang="ts">
import { TextChunk } from "@/utils/chunk";
import type { PropType } from "vue";
import "@/styles/textViewer.scss";
import AsrClient from "@/utils/client";

export default {
	name: "text-viewer",
	props: {
		client: {
			type: Object as PropType<AsrClient>,
			required: true,
		},
		textChunks: {
			type: Array as PropType<TextChunk[]>,
			required: true,
		},
	},
	computed: {
		getFinalText() {
			if (this.textChunks == undefined) return;
			const colorGradient = ["#005454", "#00887a"];
			let finalText = this.textChunks
				.slice(0, -colorGradient.length)
				.map(({ text }) => text)
				.join(" ");

			for (let i = 0; i < colorGradient.length; i++) {
				finalText += "<span style='color: " + colorGradient[i] + "'>";
				this.textChunks.at(-2 + i) == null
					? (finalText += "")
					: (finalText += " " + this.textChunks.at(-colorGradient.length + i)?.text);
				finalText += "</span>";
			}
			return finalText;
		},
	},
};
</script>
